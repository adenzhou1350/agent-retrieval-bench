import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agent_retrieval_bench import closed_tool_eval
from agent_retrieval_bench.closed_tool_eval import (
    SimpleOpenAIResponse,
    closed_tool_prefix_counts,
    evaluate_closed_tool_openai,
    run_closed_tool_llm_sample,
    select_closed_tool_samples,
)
from agent_retrieval_bench.indexed_tools import IndexedTools, load_tool_provider, parse_provider_options

FILES = {
    "src/config.py": "def parse_config(path):\n    return load(path)\n",
    "src/app.py": "from config import parse_config\nparse_config('x')\n",
    "tests/test_config.py": "def test_parse_config():\n    parse_config('y')\n",
}
SAMPLE = {
    "id": "s1",
    "task_type": "trace2code",
    "repo": "example/repo",
    "base_commit": "abc",
    "query": {"pr_title": "parse_config fails"},
    "gold": {"root_cause_files": ["src/config.py"]},
}


class FakeProvider:
    def __init__(self, hits=None, available=True, error=None):
        self.hits = hits if hits is not None else []
        self.available = available
        self.error = error
        self.calls = []
        self.prepared = []

    def describe(self):
        return {"name": "fake", "commit": "0" * 40}

    def prepare(self, *, repo, base_commit, paths):
        self.prepared.append((repo, base_commit, list(paths)))
        return {"available": self.available, "build_seconds": 1.5}

    def call(self, *, tool, arguments, repo, base_commit, limit):
        self.calls.append((tool, arguments, limit))
        if self.error:
            raise self.error
        return self.hits


class FakeResponses:
    def __init__(self, outputs, usage=None):
        self.outputs = list(outputs)
        self.usage = usage
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if self.usage is None:
            return SimpleNamespace(output_text=self.outputs.pop(0))
        return SimpleOpenAIResponse({"output_text": self.outputs.pop(0), "usage": self.usage})


def make_tools(provider, tools=("symbol_search", "references"), **caps):
    indexed = IndexedTools(provider, tools, **caps)
    status = indexed.prepare(repo="example/repo", base_commit="abc", files=FILES)
    return indexed, status


def run_policy(outputs, indexed=None, status=None, usage=None, reasoning_effort=None, require_read_submit=False):
    client = SimpleNamespace(responses=FakeResponses(outputs, usage))
    detail = run_closed_tool_llm_sample(
        sample=SAMPLE, gold_files=["src/config.py"], query_text=json.dumps(SAMPLE["query"]),
        files=FILES, model="fake-model", client=client, max_tool_calls=6, max_read_tokens=200,
        max_read_tokens_per_file=80, final_k=2, grep_top_k=3, max_model_turns=6,
        indexed_tools=indexed, index_status=status, reasoning_effort=reasoning_effort,
        require_read_submit=require_read_submit,
    )
    return detail, client.responses


class IndexedToolsTest(unittest.TestCase):
    def test_lookup_keeps_released_hits_within_caps(self):
        hits = [
            {"path": "src/config.py", "start_line": 1, "end_line": 2, "symbol": "parse_config", "kind": "function"},
            {"path": "vendor/hidden.py", "start_line": 3, "end_line": 4},
            {"path": "src/app.py", "start_line": 2, "end_line": 1, "relation": "incoming"},
            {"path": "src/config.py", "start_line": 1, "end_line": 2, "symbol": "parse_config", "kind": "function"},
            {"path": "tests/test_config.py", "start_line": 0, "symbol": "test_parse_config"},
            "not a hit",
        ]
        indexed, _ = make_tools(FakeProvider(hits), max_results=2)
        outcome = indexed.lookup(
            "symbol_search", {"symbol": "parse_config", "top_k": 50},
            repo="example/repo", base_commit="abc", files=FILES,
        )
        self.assertEqual(outcome["error"], "")
        trace = outcome["trace"]
        self.assertEqual(trace["limit"], 2)
        self.assertEqual(trace["dropped_outside_release"], 1)
        self.assertEqual([hit["path"] for hit in trace["hits"]], ["src/config.py", "src/app.py"])
        # An inverted range is dropped rather than shown.
        self.assertIsNone(trace["hits"][1]["start_line"])
        self.assertEqual(trace["omitted"], 1)
        self.assertIn("1. src/config.py:1-2 function parse_config", outcome["observation"])
        self.assertNotIn("vendor/hidden.py", outcome["observation"])

    def test_lookup_trims_hits_to_the_observation_token_cap(self):
        hits = [{"path": "src/config.py", "start_line": n, "end_line": n, "symbol": f"name_{n}"} for n in range(1, 11)]
        indexed, _ = make_tools(FakeProvider(hits), max_observation_tokens=30)
        outcome = indexed.lookup(
            "symbol_search", {"symbol": "name"}, repo="example/repo", base_commit="abc", files=FILES,
        )
        self.assertLessEqual(outcome["trace"]["observation_tokens"], 30)
        self.assertGreater(outcome["trace"]["omitted"], 0)

    def test_invalid_lookup_is_rejected_before_the_provider(self):
        provider = FakeProvider([])
        indexed, _ = make_tools(provider)
        for tool, action in (
            ("symbol_search", {"symbol": ""}),
            ("symbol_search", {"symbol": "x" * 121}),
            ("references", {"path": "missing.py", "symbol": "parse_config"}),
        ):
            outcome = indexed.lookup(tool, action, repo="example/repo", base_commit="abc", files=FILES)
            self.assertTrue(outcome["error"])
        self.assertEqual(provider.calls, [])

    def test_provider_errors_are_observed_and_prepare_runs_once(self):
        provider = FakeProvider(error=RuntimeError("index offline"))
        indexed, status = make_tools(provider)
        indexed.prepare(repo="example/repo", base_commit="abc", files=FILES)
        self.assertEqual(len(provider.prepared), 1)
        self.assertEqual(provider.prepared[0][2], sorted(FILES))
        self.assertTrue(status["available"])
        outcome = indexed.lookup(
            "references", {"path": "src/config.py", "symbol": "parse_config"},
            repo="example/repo", base_commit="abc", files=FILES,
        )
        self.assertIn("index offline", outcome["trace"]["provider_error"])
        self.assertIn("(index lookup failed)", outcome["observation"])

    def test_indexed_policy_charges_lookups_and_records_costs(self):
        provider = FakeProvider([{"path": "src/config.py", "start_line": 1, "end_line": 2, "symbol": "parse_config"}])
        indexed, status = make_tools(provider)
        detail, responses = run_policy(
            [
                '{"action":"symbol_search","symbol":"parse_config"}',
                '{"action":"references","path":"src/config.py","symbol":"parse_config"}',
                '{"action":"read_file","path":"src/config.py"}',
                '{"action":"submit","files":["src/config.py"]}',
            ],
            indexed, status,
            usage={"input_tokens": 100, "output_tokens": 10, "output_tokens_details": {"reasoning_tokens": 0}},
            reasoning_effort="none",
        )
        policy = detail["closed_tool"]
        self.assertEqual(policy["allowed_tools"], ["list_dir", "grep", "read_file", "submit", "symbol_search", "references"])
        self.assertEqual(policy["tool_calls"], 4)
        self.assertEqual(policy["index_calls"], 2)
        self.assertEqual(policy["index_calls_by_tool"], {"symbol_search": 1, "references": 1})
        self.assertEqual(policy["first_gold_step"], 3)
        self.assertEqual(policy["index_status"]["build_seconds"], 1.5)
        self.assertEqual(policy["model_usage"], {"input_tokens": 400, "output_tokens": 40, "reasoning_tokens": 0})
        self.assertGreater(policy["observation_tokens"], policy["read_tokens"])
        self.assertEqual(closed_tool_prefix_counts(detail, 2)["tool_calls"], 2)
        self.assertIn("symbol_search: definitions named `symbol`", responses.requests[0]["input"])
        self.assertEqual(responses.requests[0]["reasoning"], {"effort": "none"})
        self.assertEqual(responses.requests[0]["temperature"], 0)
        self.assertEqual(responses.requests[0]["max_output_tokens"], 700)

    def test_unavailable_index_offers_only_minimal_tools(self):
        provider = FakeProvider(available=False)
        indexed, status = make_tools(provider)
        detail, responses = run_policy(
            ['{"action":"symbol_search","symbol":"parse_config"}', '{"action":"submit","files":[]}'],
            indexed, status,
        )
        policy = detail["closed_tool"]
        self.assertEqual(policy["allowed_tools"], ["list_dir", "grep", "read_file", "submit"])
        self.assertEqual(policy["index_calls"], 0)
        self.assertEqual(policy["tool_calls"], 1)
        self.assertFalse(policy["index_status"]["available"])
        self.assertEqual(provider.calls, [])
        self.assertIn("Indexed tools are unavailable", responses.requests[0]["input"])
        self.assertIn("Action must be one of list_dir, grep, read_file, submit.", responses.requests[1]["input"])

    def test_minimal_mode_rejects_indexed_actions(self):
        detail, responses = run_policy(
            ['{"action":"references","path":"src/config.py","symbol":"parse_config"}', '{"action":"submit","files":[]}']
        )
        self.assertNotIn("index_calls", detail["closed_tool"])
        self.assertEqual(detail["closed_tool"]["tool_calls"], 1)
        self.assertNotIn("Indexed tools", responses.requests[0]["input"])
        self.assertNotIn("reasoning", responses.requests[0])

    def test_unread_submit_ends_the_episode_unless_rejection_is_enabled(self):
        unread_then_read = [
            '{"action":"submit","files":["src/config.py"]}',
            '{"action":"read_file","path":"src/config.py"}',
            '{"action":"submit","files":["src/config.py"]}',
        ]
        default, _ = run_policy(unread_then_read)
        self.assertEqual(default["closed_tool"]["final_files"], [])
        self.assertEqual(default["closed_tool"]["tool_calls"], 1)
        strict, responses = run_policy(unread_then_read, require_read_submit=True)
        policy = strict["closed_tool"]
        self.assertEqual(policy["final_files"], ["src/config.py"])
        self.assertEqual(policy["rejected_submits"], 1)
        self.assertEqual(policy["tool_calls"], 2)
        self.assertIn("submit files must already be read", responses.requests[1]["input"])

    def test_provider_loading_and_options(self):
        self.assertEqual(parse_provider_options(["a=1", "b=x=y"]), {"a": "1", "b": "x=y"})
        with self.assertRaises(ValueError):
            parse_provider_options(["novalue"])
        provider = load_tool_provider("collections:OrderedDict", {"k": "v"})
        self.assertEqual(provider["k"], "v")
        with self.assertRaises(ValueError):
            IndexedTools(FakeProvider(), ["embedding_search"])


class ClosedToolSelectionTest(unittest.TestCase):
    def _write(self, root, task, rows):
        samples = root / f"{task}.jsonl"
        samples.write_text("".join(json.dumps(row) + "\n" for row in rows))
        corpus = root / f"corpus_{task}"
        corpus.mkdir()
        chunks = corpus / "chunks.jsonl"
        chunks.write_text(json.dumps({"path": "a.py", "kind": "file", "text": "x"}) + "\n")
        manifest_rows = [
            {"repo": row["repo"], "base_commit": row["base_commit"], "status": "ok", "chunks_path": str(chunks)}
            for row in rows if row["base_commit"] != "missing"
        ]
        (corpus / "corpus_manifest.jsonl").write_text("".join(json.dumps(row) + "\n" for row in manifest_rows))
        return samples, corpus

    def test_selection_is_seeded_and_spreads_repositories(self):
        def sample(task, repo, n, **extra):
            return {
                "id": f"{task}-{repo}-{n}", "task_type": task, "repo": repo, "base_commit": "c",
                "query": {"pr_title": "x"}, "gold": {"root_cause_files": ["a.py"]}, **extra,
            }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [sample("trace2code", repo, n) for repo, count in (("r1", 5), ("r2", 1), ("r3", 3)) for n in range(count)]
            rows.append(sample("trace2code", "r4", 0, gold={}))
            rows.append({**sample("trace2code", "r5", 0), "base_commit": "missing"})
            paths = self._write(root, "trace2code", rows)

            def run(seed, name):
                return select_closed_tool_samples(
                    sample_paths=[paths[0]], corpus_dir=[paths[1]], per_task=4, seed=seed,
                    out_path=root / f"{name}.jsonl", manifest_out_path=root / f"{name}.json",
                )

            first, again, other = run("s", "a"), run("s", "b"), run("t", "c")
            self.assertEqual((root / "a.jsonl").read_text(), (root / "b.jsonl").read_text())
            self.assertEqual(first["sample_ids_sha256"], again["sample_ids_sha256"])
            self.assertNotEqual(first["sample_ids_sha256"], other["sample_ids_sha256"])
            task = first["tasks"]["trace2code"]
            self.assertEqual(task["eligible"], 9)
            self.assertEqual(set(task["selected_repos"]), {"r1", "r2", "r3"})
            self.assertEqual(sorted(task["selected_repos"].values()), [1, 1, 2])
            self.assertEqual(first["excluded"], {"trace2code:missing_corpus": 1, "trace2code:no_gold": 1})
            with self.assertRaises(ValueError):
                select_closed_tool_samples(
                    sample_paths=[paths[0]], corpus_dir=[paths[1]], per_task=10, seed="s",
                    out_path=root / "d.jsonl", manifest_out_path=root / "d.json",
                )


class RetainFailuresTest(unittest.TestCase):
    def test_failed_samples_stay_in_the_scored_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chunks = root / "chunks.jsonl"
            chunks.write_text("".join(json.dumps({"path": path, "kind": "file", "text": text}) + "\n" for path, text in FILES.items()))
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "corpus_manifest.jsonl").write_text(
                json.dumps({"repo": "example/repo", "base_commit": "abc", "status": "ok", "chunks_path": str(chunks)}) + "\n"
            )
            samples = root / "samples.jsonl"
            samples.write_text(json.dumps(SAMPLE) + "\n" + json.dumps({**SAMPLE, "id": "s2"}) + "\n")
            real = closed_tool_eval.run_closed_tool_llm_sample

            def flaky(**kwargs):
                if kwargs["sample"]["id"] == "s2":
                    raise RuntimeError("API unavailable")
                kwargs["client"] = SimpleNamespace(responses=FakeResponses(
                    ['{"action":"read_file","path":"src/config.py"}', '{"action":"submit","files":["src/config.py"]}']
                ))
                return real(**kwargs)

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), patch.object(closed_tool_eval, "run_closed_tool_llm_sample", flaky):
                summary = evaluate_closed_tool_openai(
                    sample_paths=[samples], corpus_dir=corpus, out_path=root / "summary.json",
                    details_path=root / "details.jsonl", markdown_out_path=root / "report.md",
                    retain_failures=True, mode="indexed_interactive",
                    indexed_tools=IndexedTools(FakeProvider(), ["symbol_search"]),
                )
            self.assertEqual(summary["evaluated"], 1)
            self.assertEqual(summary["scored"], 2)
            self.assertEqual(summary["closed_tool_metrics"]["overall"]["failed_samples"], 1)
            self.assertEqual(summary["metrics"]["overall"]["samples"], 2)
            self.assertEqual(summary["index_builds"][0]["build_seconds"], 1.5)
            self.assertEqual(summary["indexed_tools"]["provider"]["name"], "fake")
            self.assertEqual(len((root / "details.jsonl").read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()

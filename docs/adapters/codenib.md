# Example: CodeNib Adapter

[CodeNib](https://github.com/sysevol-ai/CodeNib) (Apache-2.0) is a
repository-context tool for coding agents. Its `codenib-arb` command ranks
files with BM25 over the released corpus and scores the rankings with this
repository's evaluator. It can also score saved rankings from another tool
without running retrieval. The adapter lives in the CodeNib repository; ARB
does not depend on it. Discussion:
[issue #2](https://github.com/eyuansu62/agent-retrieval-bench/issues/2).

This is a compatibility check, not a retrieval result. All 345 positive
samples pass the adapter's preparation step, and an eight-sample run produces
the same scores natively and on offline rescoring. A full 345-sample retrieval
run has not been made, so no scores are offered for comparison with the main
table.

## What the adapter does

The fields follow the [reporting contract](reporting_contract.md).

| Item | CodeNib static BM25 |
| --- | --- |
| Source access | Released corpus only |
| Candidates | `all_files`: every released file and symbol chunk, including tests, documentation, configuration, and extensionless files |
| Query | The `query` object as JSON with sorted keys, the same text as `query_text_for_eval`; no truncation |
| Excluded inputs | All sample fields other than `query` and the snapshot identity |
| Ranking | CodeNib's tokenizer and BM25 index rank every chunk; files keep the rank of their first chunk. This is not ARB's BM25 ranker. The full file ranking is kept for MRR. |
| Scoring | This repository at the pinned commit, run in a subprocess. CodeNib rejects a checkout with local changes under `src/`. |
| Failures | Errors and missing predictions score zero in the primary mean; valid-only means and failed IDs are reported too |
| Index | In-memory BM25 per sample; no graph or embedding index |
| Model usage | None |

One contract item is not yet met. The per-sample `retrieval_seconds` field
covers corpus loading, index construction, and the query together, and index
size is not recorded. A full run will report them separately.

## Versions

| Item | Value |
| --- | --- |
| CodeNib | commit `e3b0281e43b608a91e382e79e24e99f4a53edff3` |
| Evaluator | this repository at `07014c986f3deadb1548c62b32c0ffbe6a81465d`, unmodified |
| Dataset | `v2_code2test`, `v2_comment2context`, `v2_trace2code`, `v2_edit2ripple` from `eyuansu71/agent_retrieval_bench` at revision `5901e1ee3aff048290db72edf9c63bc498b79ea3` |

```
712b2699d3f963c2f940688ae5248304263c4ecda1b3831b2801c95712a50b85  v2_code2test/samples.jsonl
543267024f7f06127c50664a3a1b8825d3c213e4b12dbbfabf9a3346902ad796  v2_comment2context/samples.jsonl
9d0ff50155fa4f65c1bbb632abc4f1f11393c50fa7b0a9249e06128b368b6266  v2_trace2code/samples.jsonl
31d97ffe815dda8730149880c0159239a986eceb306e5a5df816dfc420717cef  v2_edit2ripple/samples.jsonl
```

## Run it

Set up the evaluator and data at their pinned revisions. The download verifies
each release archive's published checksum and needs `zstd` and `tar`.

```bash
git clone https://github.com/eyuansu62/agent-retrieval-bench /tmp/arb
git -C /tmp/arb checkout 07014c986f3deadb1548c62b32c0ffbe6a81465d
python3 -m venv /tmp/arb-env
/tmp/arb-env/bin/pip install /tmp/arb huggingface_hub

for release in v2_code2test v2_comment2context v2_trace2code v2_edit2ripple; do
  /tmp/arb-env/bin/arb download-benchmark \
    --version "$release" \
    --revision 5901e1ee3aff048290db72edf9c63bc498b79ea3 \
    --local-dir /tmp/arb-data \
    --hf-bin /tmp/arb-env/bin/hf
done
```

Install CodeNib in its own environment. Python 3.10 or newer is required.

```bash
git clone https://github.com/sysevol-ai/CodeNib /tmp/codenib
git -C /tmp/codenib checkout e3b0281e43b608a91e382e79e24e99f4a53edff3
python3 -m venv /tmp/codenib-env
/tmp/codenib-env/bin/pip install -e '/tmp/codenib[datasets]'
```

Prepare the cases, rank them, and rescore the saved rankings offline:

```bash
export PATH=/tmp/codenib-env/bin:$PATH

codenib-arb prepare --data-root /tmp/arb-data \
  --limit-per-task 2 --output /tmp/arb-run/prepared.json
codenib-arb run --prepared /tmp/arb-run/prepared.json \
  --upstream /tmp/arb --output /tmp/arb-run/bm25
codenib-arb evaluate --prepared /tmp/arb-run/prepared.json \
  --pred /tmp/arb-run/bm25/predictions.json \
  --upstream /tmp/arb --output /tmp/arb-run/rescored
```

`prepare` checks each release against its published sample count, then
freezes the selected samples and corpus hashes. `--limit-per-task 2` selects
the first two sample IDs of each task; omit it to prepare all 345. Each output
directory holds `config.json`, `predictions.json`, and `results.json`. Every
command exits nonzero if any case fails.

`evaluate` never runs retrieval. To score another tool, pass its rankings as a
JSON array or JSON Lines file with one record per sample:

```json
{"sample_id": "<released id>", "repo": "owner/repo", "base_commit": "<40-character SHA>", "status": "ok", "ranked_files": ["src/first.py", "tests/test_first.py"]}
```

Use `"status": "error"` with an `error` field for a failed sample. Unknown file
paths fail that sample.

## Compatibility receipt

| Check | Result |
| --- | --- |
| Preparation of all positive samples | 345/345 samples, 294 release/snapshot pairs (218 distinct snapshots), 0 failures |
| Smoke selection | First two sample IDs per task: 8 samples |
| Smoke retrieval and scoring | 8/8 completed |
| Native scores against offline rescoring | 64/64 metric cells and all BCY packing details identical |
| Model API calls | 0 |

Smoke means over the eight samples:

| Recall@5 | Recall@10 | Recall@20 | MRR | BCY@4k | BCY@8k | BCY@16k | BCY@32k |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.2292 | 0.4375 | 0.6250 | 0.1848 | 0.1250 | 0.2292 | 0.5000 | 0.6250 |

Eight samples cannot estimate retrieval quality, and these numbers are not
comparable with the 345-sample results in the README.

The [receipt](https://github.com/sysevol-ai/CodeNib/blob/e3b0281e43b608a91e382e79e24e99f4a53edff3/docs/assets/arb_smoke.json)
records the selected IDs, release archive and input hashes, per-sample metrics,
and fingerprints of the CodeNib files that produced them:

```
3a5c91ff6479bc96dcf2a84fac37e22ab82dfb78413bec29c0560ec1b7959602  docs/assets/arb_smoke.json
```

## Not covered yet

- A full 345-sample retrieval run with separate index and query costs.
- Selective retrieval, line and span scores, and interactive trajectories.
- Adapters for CodeNib's Zoekt, vector, and code-graph retrieval. A code-graph
  adapter would be a full-source run.

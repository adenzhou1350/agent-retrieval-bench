# Community Results

Results submitted by people outside the benchmark team. They are not part of
the main leaderboard. Each entry lists what was run, how, and where the saved
rankings are, so anyone can rescore them.

## Oko

Submitted by Bart Tyrpien, who maintains [Oko](https://github.com/bartlomein/oko)
(MIT). Discussion: [issue #1](https://github.com/eyuansu62/agent-retrieval-bench/issues/1).

Oko is a local code-search tool for coding agents. ripgrep and BM25 shortlist
function-level chunks, then TypeSafe AI's Jev reranker (a paid API that returns
one relevance score per chunk) judges up to 90 of them across three parallel
requests. No embeddings, no GPU, no index.

### Results, all 345 positive samples

Mean of three runs per version. The 0.9.1 runs are the current release. The
0.5.0 runs are the ones submitted in issue #1.

| Method | Recall@5 | Recall@20 | MRR | BCY@8k |
| --- | ---: | ---: | ---: | ---: |
| Oko 0.9.1, jev-1.14.0 | 0.4915 | 0.7019 | 0.4043 | 0.5326 |
| Oko 0.5.0, jev-1.13.0 | 0.4451 | 0.6434 | 0.3870 | 0.4809 |

Per run:

| Run | Recall@5 | Recall@20 | MRR | BCY@4k | BCY@8k | BCY@16k | BCY@32k |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.9.1 run 1 | 0.4928 | 0.6995 | 0.4063 | 0.4034 | 0.5275 | 0.6425 | 0.6976 |
| 0.9.1 run 2 | 0.4947 | 0.7034 | 0.4009 | 0.3923 | 0.5365 | 0.6415 | 0.7019 |
| 0.9.1 run 3 | 0.4870 | 0.7029 | 0.4056 | 0.4029 | 0.5338 | 0.6396 | 0.7029 |
| 0.5.0 run 1 | 0.4474 | 0.6405 | 0.3881 | 0.3913 | 0.4786 | 0.5914 | 0.6369 |
| 0.5.0 run 2 | 0.4453 | 0.6444 | 0.3889 | 0.3937 | 0.4887 | 0.5837 | 0.6434 |
| 0.5.0 run 3 | 0.4426 | 0.6453 | 0.3840 | 0.3831 | 0.4755 | 0.5875 | 0.6416 |

Per task, mean of three runs, Recall@5 / Recall@20 / MRR:

| Task | n | Oko 0.9.1 | Oko 0.5.0 |
| --- | ---: | --- | --- |
| trace2code | 101 | 0.822 / 0.901 / 0.736 | 0.712 / 0.823 / 0.673 |
| comment2context | 80 | 0.313 / 0.569 / 0.280 | 0.310 / 0.526 / 0.319 |
| code2test | 106 | 0.408 / 0.656 / 0.279 | 0.385 / 0.569 / 0.259 |
| edit2ripple | 58 | 0.315 / 0.624 / 0.226 | 0.277 / 0.628 / 0.217 |

### Dev and held-out halves

The 345 samples are split by a hash of the sample id: `dev` when the first
byte of `sha256(sample_id)` is even, `heldout` otherwise. Every details row
carries its `split`.

| Method | Split | n | Recall@5 | Recall@20 | MRR |
| --- | --- | ---: | ---: | ---: | ---: |
| Oko 0.9.1 | dev | 164 | 0.5200 | 0.7168 | 0.4418 |
| Oko 0.9.1 | heldout | 181 | 0.4656 | 0.6885 | 0.3703 |
| Oko 0.5.0 | dev | 164 | 0.4391 | 0.6404 | 0.4072 |
| Oko 0.5.0 | heldout | 181 | 0.4506 | 0.6461 | 0.3687 |

Oko 0.5.0 was tuned on the dev half only. Between 0.5.0 and 0.9.1, full
345-sample runs were one of several regression checks on some Oko changes, so
for 0.9.1 the held-out half was seen during development, though nothing was
tuned on it. MRR gained on dev and stayed flat on held-out.

### Versions

| Item | Value |
| --- | --- |
| Evaluator | this repository at `07014c986f3deadb1548c62b32c0ffbe6a81465d`, unmodified |
| Dataset | `v2_code2test`, `v2_comment2context`, `v2_trace2code`, `v2_edit2ripple` from `eyuansu71/agent_retrieval_bench` (sha256 of each `samples.jsonl` below) |
| Oko 0.9.1 | release build of commit `7209f00f4711b7150e136c5bbfa98a98e6fac260`, runs on 2026-10-22 |
| Oko 0.5.0 | commit `580fe6f`, runs on 2026-09-22 |
| Harness | `scripts/benchmark-public/replay/arb.py` in the Oko repository at the same commit as each build |
| Jev | `jev-1.14.0` for 0.9.1, `jev-1.13.0` for 0.5.0 |

```
712b2699d3f963c2f940688ae5248304263c4ecda1b3831b2801c95712a50b85  v2_code2test/samples.jsonl
543267024f7f06127c50664a3a1b8825d3c213e4b12dbbfabf9a3346902ad796  v2_comment2context/samples.jsonl
9d0ff50155fa4f65c1bbb632abc4f1f11393c50fa7b0a9249e06128b368b6266  v2_trace2code/samples.jsonl
31d97ffe815dda8730149880c0159239a986eceb306e5a5df816dfc420717cef  v2_edit2ripple/samples.jsonl
```

### Method

Source access. For each sample the harness writes a fresh workspace from the
`kind=file` rows of the released corpus at the sample's `base_commit`, so Oko
searches exactly the files in `all_files`. Oko gets no git history and no
network access to the repository.

Query. All strings in the sample's `query` object are collected, sorted
shortest first, joined with blank lines, and cut at 4,000 bytes (Oko's question
limit). Shortest first means a long diff or log is what gets cut. 60 of 345
queries are cut: 47 edit2ripple, 12 trace2code, 1 comment2context. They are
listed in [`truncated_queries.tsv`](https://github.com/bartlomein/oko/tree/9a8094edef23f0c3cb6d31ea511aa6597f430dfd/benchmarks/published/0.9.1/agent-retrieval-bench/details/truncated_queries.tsv)
and flagged as `question_truncated` in the details rows. Oko is called once per
sample with `intent: implementation`.

Ranking. The ranked list is the excerpts Oko returned first, then every
candidate Jev judged, by relevance. Oko also proposes "connected" files
that share a distinctive name with the strongest keyword matches, or are their
tests by file name. Jev judges these too, and their score is multiplied by 0.4. Chunks
are deduplicated to files in order. `top_files` holds the first 20 files and
`ranked_files` the full list, which MRR needs when the first gold file is
below rank 20.

Scoring. Recall@k and MRR come from `agent_retrieval_bench.baseline.sample_metrics`.
BCY comes from `report_bcy_budget_curve` on the stored top-20 lists.

Not evaluated. The selective-retrieval subsets were not run.

### Reranker usage and cost

A 0.9.1 run makes about 1,090 Jev requests: three per sample, plus a
fourth "recovery" request on 52 to 55 samples. It sends about 14.7M
input tokens. At Jev's list price of $0.042 per
million input tokens, with free output, one run costs about $0.62. In the three
0.9.1 runs, 9 of 3,266 requests failed in transport. No sample errored; those
samples were scored on what Oko returned. Per-request logs are in the raw
artifacts.

### Rescoring without Jev

The saved rankings are in the Oko repository at a fixed commit:
[`details/`](https://github.com/bartlomein/oko/tree/9a8094edef23f0c3cb6d31ea511aa6597f430dfd/benchmarks/published/0.9.1/agent-retrieval-bench/details). It has the six runs in the `*_details.jsonl`
layout, the truncated-query list, `rescore.py`, and `SHA256SUMS`:

```
ac9f1d4006c2b957959110bf414613b7c4478a29f934d9b34a91313aefc60e3e  oko-0.5.0-run1_details.jsonl
34dfd1d4b35fbd4c175d6ebea8764a723651994a774490c94b05e4cf8762911f  oko-0.5.0-run2_details.jsonl
85ed810eda96d6f19ac5bb548149aced45d6699f380ade192e8b52579b1df3a0  oko-0.5.0-run3_details.jsonl
c5a7f218fe1c1aead870acef2d8939da1884e0e4d30cec78f23cef41f05420cf  oko-0.9.1-run1_details.jsonl
5f3820832a2801e54a96668d4a349b74fb06a259489c1a0ca6edcc113ce05567  oko-0.9.1-run2_details.jsonl
16a82c99312a34d354fd81a3b68164808e1dd9273579b2554c7c9327311e20e3  oko-0.9.1-run3_details.jsonl
92e6cf52d3a0b0ab6238da6f544a044f21636e1cebb047bfddcbd08d8a324063  truncated_queries.tsv
114f5250031bc750ba8a23a83c050f3c7f79936e6d977b60dbdb248f465494b7  rescore.py
```

From the root of this repository, after downloading the four v2 positive
subsets:

```bash
git clone https://github.com/bartlomein/oko /tmp/oko
git -C /tmp/oko checkout 9a8094edef23f0c3cb6d31ea511aa6597f430dfd
(cd /tmp/oko/benchmarks/published/0.9.1/agent-retrieval-bench/details && shasum -a 256 -c SHA256SUMS)
python /tmp/oko/benchmarks/published/0.9.1/agent-retrieval-bench/details/rescore.py --corpus-root data/corpus
```

`rescore.py` recomputes Recall@5/20 and MRR for all, dev, and held-out from the
saved lists, checks them against the stored metrics, and runs
`report_bcy_budget_curve` on all six runs. It needs no Oko binary, no Jev key,
and no network. It gives the numbers above on both `07014c9` and `6c219ce`.

Raw outputs, with every judged candidate, its score, and per-request Jev logs:

- 0.9.1: https://github.com/bartlomein/oko/tree/9a8094edef23f0c3cb6d31ea511aa6597f430dfd/benchmarks/published/0.9.1/agent-retrieval-bench
- 0.5.0: https://github.com/bartlomein/oko/tree/1bc537a/benchmarks/published/0.5.0/agent-retrieval-bench

### RepoMap comparison

The issue compared Oko with RepoMap, Lexical, and BM25 rerun locally at
`07014c9`: 0.636 / 0.216 / 0.384, 0.494 / 0.157 / 0.265, and 0.445 / 0.152 /
0.205 (Recall@20 / MRR / BCY@8k). That RepoMap run predates the determinism fix
in #3 and is not comparable with a RepoMap rerun after it.

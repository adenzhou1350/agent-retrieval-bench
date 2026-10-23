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
| code2test | 106 | 0.408 / 0.656 / 0.279 | 0.384 / 0.569 / 0.259 |
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

## CodeNib

Submitted by the CodeNib maintainers ([CodeNib](https://github.com/sysevol-ai/CodeNib),
Apache-2.0). Discussion: [issue #2](https://github.com/eyuansu62/agent-retrieval-bench/issues/2).
The adapter and reporting rules are described in [docs/adapters](adapters/codenib.md).

CodeNib is a repository-context tool for coding agents. These are its static
retrievers, run through its ARB adapter with no model API calls. Four use only
the released corpus. A fifth, graph expansion, also indexes the full source at
each `base_commit` and is reported as a separate condition.

### Results, all 345 positive samples

One run per method; graph expansion ran as two concurrent shards (see Cost).
Means over all 345 samples; failures would count as zero, and there were none.

| Method | Source | Recall@5 | Recall@20 | MRR | BCY@8k |
| --- | --- | ---: | ---: | ---: | ---: |
| CodeNib dense | released corpus | 0.2940 | 0.5736 | 0.2425 | 0.3355 |
| CodeNib hybrid | released corpus | 0.2804 | 0.5972 | 0.2144 | 0.3101 |
| CodeNib Zoekt | released corpus | 0.2498 | 0.4400 | 0.1605 | 0.2569 |
| CodeNib BM25 | released corpus | 0.1543 | 0.3889 | 0.1211 | 0.1659 |
| CodeNib graph expansion | **full source** | 0.1543 | 0.3498 | 0.1197 | 0.1659 |

All budgets:

| Method | BCY@4k | BCY@8k | BCY@16k | BCY@32k | Recall@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| CodeNib dense | 0.2278 | 0.3355 | 0.4338 | 0.5726 | 0.4086 |
| CodeNib hybrid | 0.1746 | 0.3101 | 0.4348 | 0.5890 | 0.4169 |
| CodeNib Zoekt | 0.1449 | 0.2569 | 0.3368 | 0.4294 | 0.3358 |
| CodeNib BM25 | 0.0998 | 0.1659 | 0.2763 | 0.3831 | 0.2486 |
| CodeNib graph expansion | 0.0969 | 0.1659 | 0.2671 | 0.3444 | 0.2466 |

On the same machine, ARB's own BM25 (`eval-baseline --ranker bm25
--candidate-filter all_files`) reproduced the README row exactly: 0.4452 /
0.1520 / 0.2051 (Recall@20 / MRR / BCY@8k).

Per task, Recall@5 / Recall@20 / MRR:

| Task | n | dense | hybrid | Zoekt | BM25 | graph expansion |
| --- | ---: | --- | --- | --- | --- | --- |
| trace2code | 101 | 0.117 / 0.480 / 0.105 | 0.163 / 0.561 / 0.111 | 0.380 / 0.607 / 0.224 | 0.190 / 0.391 / 0.130 | 0.190 / 0.416 / 0.134 |
| comment2context | 80 | 0.294 / 0.550 / 0.307 | 0.354 / 0.627 / 0.258 | 0.125 / 0.325 / 0.090 | 0.229 / 0.529 / 0.177 | 0.229 / 0.506 / 0.174 |
| code2test | 106 | 0.399 / 0.690 / 0.331 | 0.286 / 0.607 / 0.266 | 0.170 / 0.304 / 0.129 | 0.090 / 0.299 / 0.078 | 0.090 / 0.209 / 0.073 |
| edit2ripple | 58 | 0.409 / 0.556 / 0.232 | 0.372 / 0.601 / 0.240 | 0.342 / 0.556 / 0.204 | 0.108 / 0.356 / 0.109 | 0.108 / 0.276 / 0.105 |

### Dev and held-out halves

The split is the one used for Oko: `dev` when the first byte of
`sha256(sample_id)` is even (164 samples), `heldout` otherwise (181).

| Method | Split | n | Recall@5 | Recall@20 | MRR |
| --- | --- | ---: | ---: | ---: | ---: |
| CodeNib dense | dev | 164 | 0.2805 | 0.5526 | 0.2340 |
| CodeNib dense | heldout | 181 | 0.3062 | 0.5925 | 0.2502 |
| CodeNib hybrid | dev | 164 | 0.3110 | 0.6105 | 0.2342 |
| CodeNib hybrid | heldout | 181 | 0.2528 | 0.5852 | 0.1964 |
| CodeNib Zoekt | dev | 164 | 0.2566 | 0.4542 | 0.1589 |
| CodeNib Zoekt | heldout | 181 | 0.2436 | 0.4273 | 0.1619 |
| CodeNib BM25 | dev | 164 | 0.1839 | 0.4233 | 0.1359 |
| CodeNib BM25 | heldout | 181 | 0.1275 | 0.3577 | 0.1077 |
| CodeNib graph expansion | dev | 164 | 0.1839 | 0.3704 | 0.1329 |
| CodeNib graph expansion | heldout | 181 | 0.1275 | 0.3310 | 0.1077 |

No method was tuned on ARB. One diagnosis used only the dev half: CodeNib's
BM25 tokenizer does not split camelCase identifiers, and splitting them closes
the gap to ARB's BM25 on dev (Recall@20 0.4233 → 0.4654). The BM25 row above
is CodeNib as released, without that change
([CodeNib #856](https://github.com/sysevol-ai/CodeNib/issues/856)).

### Methods

| Method | Index per snapshot | Ranking |
| --- | --- | --- |
| BM25 | CodeNib BM25 over every released file and symbol chunk | All chunks ranked; a file takes the rank of its first chunk |
| Dense | Exact inner-product search over `Qwen/Qwen3-Embedding-0.6B` vectors of every chunk (512 tokens, no instruction, bfloat16) | Same first-hit file ranking |
| Hybrid | Both of the above | File-level reciprocal rank fusion (k = 60) of the BM25 and dense file rankings |
| Zoekt | Zoekt trigram index of every file and symbol chunk | One literal Zoekt query per code-like term in the query (file names, backticked spans, identifiers; at most 32); files ordered by matched terms, then first match |
| Graph expansion | BM25 as above, plus a SCIP code graph of the full source | The top five BM25 files, then up to 15 released files linked to them by compiler-resolved references, then the rest in BM25 order |

**Source access.** BM25, dense, hybrid, and Zoekt read the released corpus
only. Graph expansion also builds a code graph from a depth-one checkout of
each `base_commit`: no later commits are in the object store, and the checkout
is reset and cleaned before every use. Its graph neighbors outside the
released files are dropped and counted (166 in total). BCY always uses
released text.

**Query.** The released `query` object as JSON with sorted keys, which is the
same text as `query_text_for_eval`. No truncation. No other sample field
reaches retrieval.

**Ranking.** BM25, dense, and hybrid rank every released file and symbol chunk
and keep each file at its first chunk; graph expansion reorders the BM25
ranking. Zoekt ranks only files that match a term. MRR uses the full ranking.

**Graph coverage.** A graph was built for 190 of the 218 snapshots (290 of 345
samples). Seventeen transformers snapshots and one diffusers snapshot hit
CodeNib's 600-second scip-python limit, the Java indexer produced no graph for
five spring-boot snapshots and one mockito snapshot, and two scrapy, one gin,
and one numpy snapshot produced none; those samples are ranked by BM25. On the
290 samples with a graph, graph expansion lowered Recall@20 by 0.047 against
BM25 (95% bootstrap interval −0.085 to −0.007) and left MRR and BCY@8k
unchanged. CodeNib's Go graph omits `_test.go` files, which hurts code2test.

### Cost

| Method | Cold index builds, all 218 snapshots | Largest index | Query median / p95 | Tool calls per sample |
| --- | ---: | --- | --- | ---: |
| BM25 | 437 s | 160k chunks, 13.4M tokens, in memory | 0.40 s / 11.97 s | 1 |
| Dense | 4,035 s | 160k vectors, 665 MB, in memory | 0.15 s / 1.76 s | 1 |
| Hybrid | 4,365 s | both of the above | 0.55 s / 11.96 s | 2 |
| Zoekt | 1,315 s | 276 MB on disk (9.2 GB in total) | 0.67 s / 2.37 s | 14.4 |
| Graph expansion | 22,541 s, plus 419 s fetching source | 160k vertices, 343k reference edges | 0.33 s / 9.16 s | 1.8 |

No method made a model API call. Dense and hybrid ran the embedding model
locally and embedded each distinct chunk text once per run: 0.90M of the 6.2M
released chunks were embedded and the rest reused. Graph expansion ran as two
concurrent shards of the same commit on disjoint snapshots.

One host: Intel Xeon Gold 5416S, 64 cores, and one H100. The CPU and GPU
methods ran at the same time on this host, which other jobs also shared, so
treat timings as indicative.

### Versions

| Item | Value |
| --- | --- |
| Evaluator | this repository at `07014c986f3deadb1548c62b32c0ffbe6a81465d`, unmodified |
| Dataset | the four v2 positive releases at revision `5901e1ee3aff048290db72edf9c63bc498b79ea3`; `samples.jsonl` checksums as listed for Oko above |
| CodeNib | tag [`arb/2026-10-22/methods`](https://github.com/sysevol-ai/CodeNib/tree/arb/2026-10-22/methods) (commit `7376fe45`) |
| Dense model | `Qwen/Qwen3-Embedding-0.6B` at revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` |

### Rescoring without running CodeNib

The rankings, a receipt with every per-sample metric, and `rescore.py` are
published as a Hugging Face dataset at a fixed revision:
[`sysevol-ai/codenib-arb-rankings`](https://huggingface.co/datasets/sysevol-ai/codenib-arb-rankings/tree/5310148b0d10096fd8ca4d418ef0be510153cdfc).

```
941f08ef09ef456dc8580b465cb4a412e75a4db92376e739a367fbe1a883f77f  bm25_predictions.json.gz
6469808065f512d7f65982cddc80e2df6384c1530c211fd3ea0057b4ccd54d46  dense_predictions.json.gz
22acd331efb155d1248a172a81c19da9c5821732123667997d03dc4c9f8b1e09  graph_expansion_predictions.json.gz
6a5e71a078d262bd9140dcd6ffa03ff1353cf584a5700fab0daace70cb29d2ac  hybrid_predictions.json.gz
dfcd319066b2715043fa0504ee69e8a4990296af0e02a2f022916c029f7ee342  zoekt_predictions.json.gz
```

From the root of this repository, after downloading the four v2 positive
subsets into `data/`:

```bash
hf download sysevol-ai/codenib-arb-rankings --repo-type dataset \
  --revision 5310148b0d10096fd8ca4d418ef0be510153cdfc --local-dir codenib-arb
(cd codenib-arb/rankings && sha256sum -c SHA256SUMS)
python codenib-arb/rescore.py --rankings codenib-arb/rankings \
  --expected codenib-arb/arb_full.json
```

`rescore.py` imports only this repository's evaluator. It recomputes
Recall@5/10/20, full-ranking MRR, and canonical BCY for every method; graph
expansion rankings are first limited to released files. It needs no CodeNib
install, no model, and no network after the download. On `07014c9` and on
`3942629` it reproduces all 2,760 per-sample metric cells of each method.

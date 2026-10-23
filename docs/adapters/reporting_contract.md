# Reporting a Retrieval Adapter

An adapter runs a retrieval tool from outside this repository on the four
positive tasks and scores its file rankings with this repository's evaluator.
This page lists what a report should state so that adapters can be compared
with each other and with the built-in baselines.

The contract covers static file rankings. Selective retrieval and interactive
tracks are out of scope. [CodeNib](codenib.md) is a worked example.

## Source access

Every report names one of two conditions. Scores from different conditions
belong in separate rows or tables.

| Condition | What the retriever may read |
| --- | --- |
| Released corpus | The released corpus snapshot for each sample, as used by the built-in baselines |
| Full source | A clean checkout of the sample's `repo` at its `base_commit`, in addition to the released corpus |

The corpus builder truncates long files, so a full checkout gives the
retriever more information. Compiler-based code graphs usually need one. A
full-source run must:

- be labeled as full source wherever its scores appear;
- give the retriever the working tree at `base_commit` without later history.
  A full clone's object store contains the resolving commit;
- keep gold labels and the resolving change out of retrieval inputs and
  indexes;
- score only files in the sample's released candidate set. Remove other paths
  before cutoffs and report how many were removed;
- compute canonical BCY on the released `kind=file` text, not on the checkout.

## Inputs

**Query.** Only the sample's `query` object and its snapshot identity (`repo`,
`base_commit`) may reach the retriever. Other fields, including `gold`,
`gold_blocks`, `gold_spans`, `hard_negative_files`, `audit`, and `metadata`,
can reveal the answer: `metadata` records the PR, fix commit, or changed files.
State how the query object becomes text, for example JSON with sorted keys, and
report any truncation with the number of truncated queries.

**Candidates.** The official candidate set is `all_files`: every released file,
including tests, documentation, and configuration. A task-aware filter is a
diagnostic ablation and should be reported as one.

**Tuning.** State whether the tool, its prompts, or its parameters were tuned
on ARB samples, and on which ones.

## Rankings and scores

Score with this repository's evaluator at a stated commit rather than a
reimplementation of the metrics.

| Score | Ranking it uses |
| --- | --- |
| Recall@5, @10, @20 | The first k distinct files. Duplicate paths collapse at their first occurrence before cutoffs. |
| MRR | The full supplied file ranking. A truncated ranking can lower MRR, so report ranking depth. |
| BCY@4k, @8k, @16k, @32k | Canonical token-based packing of the first 20 distinct files, using released `kind=file` text. The legacy `gold_coverage@8k` field is not canonical BCY. |

## Denominator and failures

Report the selected case set: all 345 positive samples, or a stated selection
rule together with the selected sample IDs.

Failures stay in the denominator. A sample with no prediction or a retrieval
error scores zero in the primary mean. Report the mean over valid samples and
the failed sample IDs next to it. An explicit empty ranking is a valid
zero-score result, not a failure.

A run on a small subset is a compatibility check. Do not place its scores next
to full-run results.

## Cost

Report each quantity on its own. Index construction is not part of query
latency.

| Quantity | What to report |
| --- | --- |
| Cold index construction | Wall time and index size, per snapshot or in total; hardware; whether indexes are shared by samples with the same snapshot |
| Query latency | Per-sample retrieval time once the index exists |
| Tool calls | Retrieval or tool invocations per sample |
| Model usage | Model IDs, API requests, input and output tokens, and cost; zero when no model is called |
| Context budget | Context tokens the tool returns per sample, if it packs context itself |

## Reproducibility

- Pin the evaluator commit, the dataset revision, and the tool version, and
  list the `samples.jsonl` checksums.
- Publish the full per-sample rankings with checksums, so that anyone can
  rescore them without running the tool. They can live in the tool's own
  repository at a fixed commit.
- Give the commands that produce the rankings and the command that rescores
  them.

## Interactive comparisons

An indexed-interactive comparison gives an agent indexed tools, such as symbol
search or relationship expansion, and compares it with iterative grep-style
search. It is a separate follow-up track. It should hold the agent model and
budgets fixed, and it is distinct from the minimal closed-tool diagnostic,
which offers only `list_dir`, `grep`, `read_file`, and `submit`.

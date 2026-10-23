# Indexed Tools in the Closed-Tool Loop

The `indexed_interactive` mode measures whether a policy uses index lookups
well when it chooses them itself. It runs the same evaluator-mediated loop as
the closed-tool diagnostic and adds one or both of these tools:

| Tool | Arguments | Returns |
| --- | --- | --- |
| `symbol_search` | `symbol` | Definitions with that name, as path and line range |
| `references` | `path`, `symbol` | Locations that reference, or are referenced by, that symbol, as path and line range |

Lookups return locations only. Reading content still costs `read_file` calls
and read tokens, so context accounting matches the minimal-tool mode. The
minimal-tool mode (`--mode closed_tool`, the default) stays available
unchanged.

## Plugging in a provider

ARB does not depend on any index library. A provider is a Python object that
`--tool-provider module:callable` creates; each `--tool-provider-option
key=value` becomes a keyword argument of the callable. An MCP-backed index
needs a small callable that forwards these calls to its server.

```python
class Provider:
    def describe(self) -> dict: ...  # optional; identifies the build in the summary
    def prepare(self, *, repo, base_commit, paths) -> dict: ...
    def call(self, *, tool, arguments, repo, base_commit, limit) -> list[dict]: ...
```

`prepare` runs once per snapshot. `paths` is the released file list. It returns
`available` and may add `build_seconds`, `cached`, `size`, and `reason`. When
`available` is false, or `prepare` raises, the policy sees only the minimal
tools for that sample and the prompt says the index is unavailable.

`call` receives `{"symbol"}` for `symbol_search` and `{"path", "symbol"}` for
`references`. Each hit has `path` and may have `start_line` and `end_line`
(1-based, inclusive), `symbol`, `kind`, and `relation`.

The provider never receives the sample id, the query, or gold labels.

## What the evaluator enforces

- Only the tools named in `--indexed-tools` are offered.
- An answered lookup costs one call from the shared `--max-tool-calls` budget.
  Lookups with a missing symbol, or a `references` path that is not a released
  file, are rejected without charge, like other invalid actions.
- Hits outside the released files are dropped and counted.
- At most `--max-index-results` hits are shown (default 10), and hits are
  trimmed until the observation fits `--max-index-observation-tokens` (default
  400, counted with the charged code tokenizer).
- A provider exception is shown to the policy as a failed lookup and still
  costs the call.

## What a run records

Each trajectory records index calls by tool, index observation tokens,
provider errors, and the snapshot's index status. Every OpenAI policy run also
records model input and output tokens from the Responses API and the tokens of
all observations. The summary reports the provider's `describe()` output, the
per-snapshot index builds, the policy settings, and the harness commit. Index
build time is a per-snapshot cost and is reported separately from the policy
run.

With `--retain-failures`, a sample whose policy run raises scores as empty
context, so the denominator stays the selected set. The details file keeps
only completed trajectories, and resuming retries the failed samples.

By default, a submit that names no file already read ends the episode with
empty context. With `--require-read-submit`, that submit is rejected without
charge and the policy continues; each trajectory counts its rejected submits.

## Running arms on a frozen sample set

`select-closed-tool-samples` freezes a per-task sample set before any policy
runs. It keeps samples that have gold files, no query leakage, and a released
corpus snapshot. Within each task, repositories take turns in a seeded hash
order, so every repository gets one sample before any gets two. It reads no
method scores and builds no index.

```bash
TASKS="code2test comment2context edit2ripple trace2code"
arb select-closed-tool-samples \
  $(for t in $TASKS; do echo data/benchmark/v2_$t/samples.jsonl; done) \
  $(for t in $TASKS; do echo --corpus data/corpus/v2_$t; done) \
  --per-task 15 --seed <seed> --out pilot_samples.jsonl --manifest-out pilot_manifest.json

# Arm A: minimal tools. Arms B and C add --mode indexed_interactive,
# --indexed-tools symbol_search (B) or symbol_search,references (C),
# and --tool-provider with its options.
arb eval-closed-tool-llm \
  $(for t in $TASKS; do echo data/benchmark/v2_$t/samples.jsonl; done) \
  $(for t in $TASKS; do echo --corpus data/corpus/v2_$t; done) \
  --keep-list pilot_samples.jsonl --model <dated snapshot> --reasoning-effort none \
  --retain-failures --out summary_A.json --details details_A.jsonl --markdown-out report_A.md
```

Repeat `--corpus` once per samples file to pair each release with its own
corpus. Run every arm with the same model, reasoning effort, budgets, and
sample set.

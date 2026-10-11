# Controlled test-generation trials

This complements the existing runtime benchmarks. It asks whether supplying framework context changes the quality, generation time and token cost of newly generated tests on the existing sample CRM and Java customer-risk API.

## Current protocol: one-response-mutation-v1

Two tasks, baseline and framework conditions, three repetitions each (12 model calls). Alternate arm order within each application. Freeze application and helper hashes, requirements, model alias, reasoning effort, CLI version and time budget before generation. Each trial starts a fresh ephemeral CLI session with tools disabled. Both conditions receive the same application source and acceptance criteria. The framework condition additionally receives the actual fixture/page/assertion helpers (CRM) or shared Java QA helpers (API), with relevant conventions. The baseline uses plain Playwright or RestAssured APIs. Both use the same dependency versions.

The model returns one complete source file. Do not repair its output. Run that exact file against the healthy app, then against each isolated fault. Existing oracle tests and hidden fault definitions are not in the generation prompt. The real application runs behind a local fault-injection proxy; only the intended response is changed. An injected fault counts as detected only when it was actually activated and the submitted suite produces an assertion failure, without execution errors. A timeout, compilation failure, empty suite or infrastructure failure cannot count as detection. Correct completion requires the healthy suite and every fault check to pass. Fault coverage is a finite synthetic quality measure, not exhaustive correctness.

CRM faults: viewer export returns 200, wrong denial JSON, enabled export button, missing read-only banner. API faults: wrong low category, medium score, high eligibility, customer ID, decision reason, accepted missing ID, accepted blank ID. Tests run with one worker, no retries. Source code of the product and helpers is unchanged.

## Measurements

- **Completion:** all healthy and fault checks passed. Show numerator and denominator.
- **Quality:** individual healthy/fault checks passed, independently of binary completion.
- **Time:** observed CLI wall time and evaluation wall time separately. Machine/provider load is not controlled; no causal speed claim.
- **Human corrections:** unavailable until a person reviews and corrects a frozen submission. Automatic validation is not human correction. No fabricated zero.
- **Cost:** reported CLI input, cached-input and output tokens; standard API-equivalent USD estimate from dated official rates. Actual billed spend is unavailable for the signed-in CLI. This estimate does not include subscription allocation or infrastructure.
- **Provenance:** prompt, source, response, event and evaluator hashes. Model alias is recorded; an immutable backend snapshot is not exposed by the CLI.

This is a small context-assisted generation pilot. It does not measure the complete agentic planner/capture/repair workflow, JEV model quality, developer productivity, production reliability or financial return. Larger and harder tasks plus a timed human review are needed before those claims.

## Run locally

Use Python 3, the authenticated Codex CLI, Node 22, Playwright/Chromium already installed in the harness, and the API repository's Java/Maven prerequisites. Execute from the dashboard checkout; substitute your checkout/output paths. The output directory contains private raw evidence and must remain outside Git.

```sh
python3 trials/run.py prepare --output ../private-campaign --harness ../playwright-harness-framework --api ../agentic-workspace
python3 trials/run.py generate --output ../private-campaign
python3 trials/evaluate.py --output ../private-campaign
python3 trials/publish.py --output ../private-campaign --project harness
python3 trials/publish.py --output ../private-campaign --project api
```

Generation and evaluation resume completed trial records without replacing them. Generation stops on provider/runtime failure; inspect the retained evidence before explicitly resuming. Never discard a model failure and replace it with a better run. Publication exports only the explicit public schema to `benchmark-results/trials.json`, retaining campaigns by hash. Runtime benchmark publishers preserve that file. The dashboard reads both trial feeds automatically every minute; no import or redeploy is needed for subsequent campaigns. Only code/layout changes need deployment.

Raw prompts, model code, provider event streams, test logs and machine paths stay private. Review generated code before executing it; the lexical checks in this runner are protocol guards, not a security sandbox. The evaluator is designed for these public synthetic tasks, not arbitrary untrusted submissions.

## First campaign implementation notes

The outer filesystem sandbox initially prevented CLI initialization before any model request. That startup failure is retained separately. The approved CLI execution uses read-only model sandboxing and disabled shell tools. One grader field-name collision was corrected before completed grading; generated submissions were not changed. Generation and grading overlapped on the same machine for part of the campaign, so measured wall times are descriptive only.

Official references: [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode), [systematic skill evaluation](https://developers.openai.com/blog/eval-skills), [GPT-6.1 Sol rates](https://developers.openai.com/api/docs/models/gpt-6.1-sol), verified 11 October 2026.

## Local llama.cpp / Gemma API track

Reuse the API prompts and scoring plan from an existing cloud campaign. The local generator inspects the existing loopback server and requires the workspace's Gemma 4 E2B IT QAT UD-Q4_K_XL file, 8192-token context and one slot. It fingerprints the loaded GGUF file and records hardware, server defaults, model snapshot, temperature 0.2, repeat seeds 1–3, disabled prompt cache reuse and maximum 4096 output tokens. It does not download a model, restart the server or modify its configuration.

```sh
python3 trials/local.py prepare --cloud ../private-campaign --output ../private-local-campaign
python3 trials/local.py generate --output ../private-local-campaign
python3 trials/evaluate.py --output ../private-local-campaign
python3 trials/publish.py --output ../private-local-campaign --project api
```

The publisher detects the local runtime and writes `benchmark-results/local-trials.json`, preserving the cloud campaign in `trials.json`. The dashboard reads both independently. Report measured prompt/output tokens, wall time, generation tokens/second, healthy-app checks and fault detection. No external inference API fee is incurred by these loopback calls; total operating cost is **unknown**, not zero. Electricity and hardware depreciation are not instrumented.

This is the generation slice of the local Pi + llama.cpp architecture. Pi's tool-calling/editing loop is not exercised by this protocol. Within-local baseline/framework comparisons share model and request settings. Cloud/local comparisons also change the model, tokenizer and provider wrapper, so a difference cannot be attributed only to locality or hardware. The local model is already loaded; cold-start and model-loading time are excluded.

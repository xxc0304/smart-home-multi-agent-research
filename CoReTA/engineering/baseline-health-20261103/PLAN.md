# V20 baseline precision diagnostic — prepared, not launched

Goal: check whether NF4 quantization materially changes the observed weak baseline before interpreting expert advantage in teams. This is a bounded development diagnostic, not a search for the highest-scoring baseline.

## Fixed scope

- Use the first 20 IDs in the existing ordered V200 validation.inputs.jsonl. Freeze their IDs, input bytes and SHA-256 on the server before execution; do not select by prior correctness.
- Baseline only, no adapter. Same locally cached Qwen3-4B revision 1cfa9a7208912126459214e8b04321603b3df60c.
- Compare NF4/bfloat16 with unquantized bfloat16, in separate sequential processes. Same task projection, system message, answer suffix, tokenizer/template, enable_thinking=false, seed20261102, greedy and 256 output-token cap as the completed B0 V evaluation.
- Exactly 20 generations per condition, at most 40 new generations. Maximum 600 seconds per condition and 1800 seconds for the whole GPU job; the outer process timeout must enforce the total bound. No retries, expansions, training, model downloads or thinking-mode arm.
- Preserve raw responses, EOS/output-limit/failure state, prompt and output lengths, elapsed time and CUDA memory statistics. Score all complete answers with the existing official answer scorer; preserve invalid/missing items explicitly and do not report a complete primary mean if incomplete.
- Report paired per-item EM/F1, answer agreement, technical failures, truncation and cost; compare the NF4 prefix with the immutable historical V baseline for implementation drift. Never alter original scores.
- No C160/H reads, no C-based tuning and no B1 launch in this batch.

## Completion and interpretation

Deliver frozen manifest/config/code hashes, actual execution records, paired result summary and assistant stage review. A difference can reveal sensitivity under this fixed condition; 20 development items cannot establish overall model capability, causal reasoning gains, optimal decoding, or team benefit. No difference does not rule out precision effects outside this prefix.

## Readiness as prepared locally

Scientific meaning: PASS for this bounded sensitivity check.
Execution readiness: BLOCKED pending tool-accessible SSH authentication, server working-tree/environment inspection, frozen input/config/code bindings, exact prompt/token replay against historical V outputs, full selected-input length validation, available GPU memory and timeout/failure export checks.
Overall: DO_NOT_RUN until the affected preparation checks pass and a batch-specific EXPERIMENT_REVIEW.md records the evidence. The user's instruction to begin authorizes preparation and this finite diagnostic; it does not authorize unrelated training or expanded experiments.

Reviewer: assistant self-review only, not independent review.

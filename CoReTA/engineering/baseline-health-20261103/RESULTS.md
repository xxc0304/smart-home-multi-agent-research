# V20 baseline precision diagnostic — 2026-11-03

Actual remote execution completed with exit0, 40/40 valid responses, 37.29 seconds pipeline wall time. Run: `runs/baseline-health-v20-20261103-v1`. Local evidence copy: `evidence/baseline-health-v20-20261103-v1/`.

| Condition | Valid | EM | F1 | Arm wall time | Peak allocated |
|---|---:|---:|---:|---:|---:|
| NF4/bfloat16 | 20/20 | 3/20 (15%) | 20.50% | 14.95s | 3.28GiB |
| Unquantized BF16 | 20/20 | 2/20 (10%) | 20.31% | 13.68s | 8.33GiB |

Same first20 existing V200 IDs, model revision, complete inputs, tokenizer/template, answer suffix, nonthinking and greedy256. No adapter, training, downloads, paid API, retries, C/H reads or team generation. Maximum selected input3696 tokens. Historical code/config/data hashes matched; no original artifacts changed.

Paired: both correct2, NF4 only1, BF16 only0, both wrong17. Raw answers agree12/20. New NF4 responses match historical V responses20/20. Both arms had0 allocator retries,0 OOMs, no output-limit or technical failures. GPU after completion:2MiB used,0% utilization.

## Interpretation and stage review

PASS for the bounded precision diagnostic and faithful execution. The small prefix provides no evidence that replacing NF4 with BF16 fixes the observed weak baseline. It does not show BF16 is generally worse, prove quantization irrelevant, establish an optimal baseline, isolate reasoning from format, or establish team effects. Eight raw answers changed even though net EM changed by only one item.

Retain the original NF4 setup and C160 qualification under its stated condition; no basis here to replace the model or rerun C. The next useful stage is matching independent B/E answers to the actual team output requirements and preflighting full-history length, adapter switching, finite cost and review binding before1–2 full four-arm timing items. No B1 batch was launched here. Thinking-mode experiments remain separately proposed rather than silently added.

Review: assistant self-review, review_independence=none/provisional. This is development evidence, not independent review or a paper-level precision comparison. Evidence: frozen manifest/config/code, PREFLIGHT.json, bound APPROVAL.json, raw responses, per-item official scores, memory/execution records, RESULTS.json and PIPELINE_STATUS.json. Source state on the server includes existing uncommitted work; it was preserved, with no git pull/reset. Dedicated notebook SSH key authentication was separately authorized and verified; no private key or password was copied into this repository.

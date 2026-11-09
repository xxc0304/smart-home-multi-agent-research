# D32 first-pass readout — retrieved 2026-11-04

Retrieved over SSH after switching notebook to a phone hotspot. No model generations, remote changes or reruns were performed during retrieval. Server originals remain authoritative; summary evidence downloaded to `evidence/final/`.

## Completeness and technical status

Supervisor ended2026-11-04 03:09:24+08:00 with STOPPED/exit2 because the final completeness gate found four incomplete items, not because the job stopped before visiting32 items. Planned32,recorded32,complete four-arm pairs28.1584 actual cumulative requests:1580OK/4OUTPUT_LIMIT. Prior8 traces inherited byte-identically; adapter routes matched. Final scorer status INCOMPLETE and primary_enabled=false. GPU idle after retrieval (2MiB,0%). New30-item stages took roughly2.5h total; final24-item stage7116.41s.

Truncations: `2hop__342640_126084` initial/M3/cap256; `2hop__638478_377891` work/A/M3/cap512; `2hop__130557_70090` work/C/M3/cap512; `2hop__107379_20644` work/B/M2/cap512. Raw outputs and partial dependent paths retained; no replacements or retries. Four incomplete items are12.5% of planned items, so complete-case analysis may be selective.

## Descriptive results on the SAME28 complete items only

| Arm | Condition | Expected team EM | Seeded actual correct | Expert final correct | Expert correct→wrong | Expert wrong→correct |
|---|---|---:|---:|---:|---:|---:|
| A | Private, hidden |51.79%|14/28|16/28|4/19|1/9|
| B | Discussion, hidden |64.29%|18/28|19/28|3/19|3/9|
| C | Private, revealed |56.25%|16/28|18/28|3/19|2/9|
| D | Discussion, revealed |57.14%|16/28|19/28|2/19|2/9|

Expert initial EM19/28=67.86%; expert-initial-wrong denominator9. Expected and seeded actual differ because tied highest-vote classes are sampled uniformly; expected EM is the registered primary readout, but no complete32-item primary result is enabled here. This table is descriptive complete-case evidence, not a repaired or complete primary score.

Observed on this subset: hidden discussion B has the highest team score among the four conditions, but18/28 remains below the expert's initial19/28. Expert corrections and harmful changes both occur; equal net expert accuracy in B or D does not mean no revision or harm. Role-disclosure effects differ between private and discussion conditions; do not infer a universal identity effect or unique internal mechanism. These are32 fixed development items with only28 complete; not final confirmatory evidence or independent causal annotation.

## Stage review

Assistant review: execution records and preserved-prefix/route evidence support this first-pass readout; technical completeness REVISE. Preserve original v2 data, investigate the four truncated outputs before any new protocol or large batch, and consider separately versioned throughput/termination checks. User explicitly requested finishing this batch before acceleration; no acceleration or additional experiment launched. Existing server automated stage review is assistant-authored fixed checks, independence=none/provisional. Do not quietly resume incomplete records, discard them from the planned denominator, or claim all32 complete.

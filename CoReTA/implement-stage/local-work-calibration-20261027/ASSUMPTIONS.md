# Assumption Ledger

ASK=never. Declare choices before implementation. Defaults chosen by executor; not new user model-API authorization.

| ID | Underdetermined | Chosen | Class | Source |
|---|---|---|---|---|
| C-001 | Calibration cases | main-01 first frozen random case; diagnostic-01 first separately frozen supplement. No success-based choice. Neither is a new confirmatory result | semantic | default |
| C-002 | Arms/order | main ordinary/local_work/single; diagnostic local_work/ordinary/single. One run each, seven response slots each, no expansion | semantic | default |
| C-003 | Limits | Max42 calls, total output82944 tokens, total input688128 (=42x16384), per input16384 tokens (existing local tokenizer estimate+256), per output2048 or1536 per schedule | interface | default |
| C-004 | Transport | Existing DeepSeekClient, official https://api.deepseek.com/responses, deepseek-flash, temperature0.7, reasoning none, zero retries, 120s request timeout | interface | default |
| C-005 | Failure | Unreadable/missing core blocks that flow's later waves, finish same-wave sibling unless system/global stop; continue independent frozen flows; two consecutive unreadable cores stop batch. Transport/unknown usage/budget anomalies stop batch immediately | interface | default |
| C-006 | Freeze | Bind runtime case/config/source/schema builders/tokenizer to manifest and preflight, new output dirs, no resume/retry; fail if bound inputs/code changed | interface | user |
| C-007 | Cost | Reserve attempted estimated input and full output cap before each call; verify actual usage and each total; missing usage remains unknown and stops, no fabricated zero cost | semantic | default |
| C-008 | Review meaning | Local fixtures validate request/response envelope and orchestration, historical outputs validate old core/source carriers only. First new-schema live batch is explicitly protocol qualification, not prior format stability or final gain proof | semantic | default |
| C-009 | Gold isolation | Runtime prepared cases contain only original task/source; no answers/derivations/annotations/selected correct operations. Offline scoring only after batch using separate source files | semantic | default |
| C-010 | Authorization | Live path requires batch-specific authorization record bound to manifest and scope; local fixtures require explicit injected transport and never network | interface | user |
| C-011 | Analysis | Main and diagnostic separate, include failed/not-run flows, no pooled 2-task efficacy. Report natural work formation, bindings, uses and semantic review before expansion | semantic | user |
| C-012 | Failure counting point | Count core readability per response in actual call order; stop immediately on second consecutive unreadable, preserving any same-wave replies already received | interface | default |
| C-013 | Local transport fixture | Deterministic hand-authored JSON plus DeepSeek-shaped response/usage envelopes, labelled fixture. It can test dynamic work/binding flow but never establish semantic accuracy | semantic | default |
| C-014 | Gate scope | Fixture-only preflight/review cannot authorize live entry. verify defaults to bounded_protocol_calibration, allows local_fixture_only only on explicit local_fixture path; checker restores fixture gate in finally after a temporary authorization-test gate | semantic | sweep |
| C-015 | HTTP body preservation | Batch adapter preserves exact HTTP response bytes before decoding JSON, including error/invalid JSON bodies and partial bytes exposed by IncompleteRead; no credentials/headers written. Do not modify old shared model_client or frozen experiments | interface | sweep |

This is continuation of research-implement-feature with bounded implementation and same-family provisional sweep. No external sends are authorized by this ledger itself.

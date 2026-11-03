# Fixed-artifact review probe

Base commit: 00338a49953246eaeff582e1a16f4c2959b77374. ASK=never, effort=balanced.

Implement a bounded replay of the eight actual review requests from four units in workboard-d0-natural-live-20261022-r2. A replays the original payload. B replaces only the relevant base review duty with the approved generic duty text from REVIEW_REPLACEMENT_DESIGN_20261023.md. Preserve packet, schema, member, source access, all other instructions and generation settings. Each input is run twice per condition, for 32 requests maximum and 98304 output tokens. Reviews remain mutually independent. No TRY, CHOOSE or gold loading.

Outputs: prepared payloads and manifest; new live directory with requests/responses/decoded outputs, status and complete usage; separate manual semantic audit. First technical error stops the batch, no retries/repairs/resume. Existing official DeepSeek API and tokenizer are reused.

Success commands: offline test suite for this tool; prepare CLI; explicit run CLI with --live. Offline success proves execution integrity only. The live probe tests reviewer discrimination on two selected development tasks, not final solution efficacy.

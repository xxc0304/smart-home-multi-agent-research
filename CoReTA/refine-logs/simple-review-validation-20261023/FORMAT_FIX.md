# Format fix — 2026-10-23

Decision before code: attempt4 contains two distinct complete JSON objects in one output_text, not truncation. Both cannot be silently merged/selected. Keep old raw run unchanged and strict decoding.

Scope: current/plain probe only. Both conditions use the same documented Responses text.format=json_object plus an identical single-object instruction in input; OUTPUT_SCHEMA remains byte-identical in instructions, used for local strict validation. No strict=true assumption (not documented for this endpoint), new calls, retries, repairs, token cap or reasoning changes. This changes transport formatting in both conditions and requires a new frozen preparation; C is historical B plus the shared format envelope, not byte-exact historical B.

Runner supports the declared json_object policy using the schema already in OUTPUT_SCHEMA, verifies consistency before transport, and still stops at first error. Historical json_schema preparations remain supported. Frozen old preparation is not edited. New preparation is offline and does not authorize launch.

Reference: https://api-docs.deepseek.com/api/create-response/ documents json_object and json_schema under text.format. Offline tests establish wiring and rejection behavior, not guaranteed future model compliance.

Implementation notes: historical source verification explicitly permits only the revised shared runner, whose historical digest is pinned (53d190adb519cfa11893a0da325a460deb6cacffe8b814e9b9cf70dbafab56eb). All other old sources and all historical payload hashes must match. New preparation hashes the current runner. Old batches now stale by design, not runnable as if unchanged.

Validation: 4 simple-probe tests passed (6.080s), including real attempt4 offline replay rejected with known usage preserved, 32 scripted calls, equal formatting across C/S, and malformed/duplicate-key/schema failures. Existing 5 runner tests passed (7.183s), including first-error stop, incomplete response, unknown usage, payload tampering, exact historical JSON-schema payloads. Initial new-test run correctly failed on old runner hash; resolved with the explicit pinned lineage exception above. No new DeepSeek requests. Actual future JSON-mode compliance remains untested.

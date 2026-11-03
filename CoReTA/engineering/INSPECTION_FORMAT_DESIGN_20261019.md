# Inspection format repair

Separate inspection_format_v1 variant, no historical source changes. Generate exact field lists from the existing ClosureInspection schema and show them at inspection time, explicitly distinguishing checks.scope from closure_reviews (no scope/check_id). No schema relaxation, automatic field removal, semantic mutation, or extra retries. A client subclass adds JSON decoder message/line/column/offset to existing bounded repair feedback; raw outputs remain in original logs. Preserve version/hash, objection coverage, visible references, and pending-only review checks.

Offline tests must replay both real 156 failures and 592 extra check_id, verify rejection and informative feedback, then exercise one scripted bounded repair. This demonstrates protocol handling only. Freeze the same six seen tasks for one live regression, without reruns, retaining every failure and scoring last delivered artifacts.

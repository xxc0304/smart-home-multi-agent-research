# Assumption Ledger

ASK mode: never. Decisions below precede code. Sources default unless explicitly stated.

| ID | Under-determined | Chosen | Class | Source |
|---|---|---|---|---|
| A-001 | First task family | TAT-QA official train split for adapter/development only; dev/test untouched | semantic | default |
| A-002 | Resource partition | Two members: complete original table vs all original paragraphs, preserving headers and text; swap identities as a separate assignment | semantic | default |
| A-003 | Task selection | First six arithmetic table-text questions in upstream file order, at most one per context; selection uses task-type annotations only, never model success or numeric answer | semantic | default |
| A-004 | Meaning of offline success | Scripted events prove executor/interface behavior only; real historical replies prove common-interface compatibility, never new-operation generation or method gain | semantic | user |
| A-005 | Expression support | Numeric finite arithmetic +,-,*,/ and parentheses using named inputs; explicit unit labels, conversions expressed by model operations; no arbitrary code or hidden task rules | interface | default |
| A-006 | Semantic matching | Input bindings require explicit work-owner decision; entity/period/unit compatibility uses declared metadata only, not truth validation | semantic | default |
| A-007 | Unknown and uncertain inputs | Missing values wait, never zero/false; output inherits conditions; binding may be conditional but never upgraded automatically | semantic | user |
| A-008 | Source access | Work sources must be own or previously disclosed; disclosure copies original passages from host handles; no model quote regeneration required | interface | default |
| A-009 | Updates | Author can version own work/bindings; alternatives may be new work by another member; invalidate dependent outputs, preserve unaffected work; no physical deletion | interface | default |
| A-010 | Failures | Unreadable core isolated, invalid individual operations recorded without dropping valid siblings; no network calls/retries in this build | interface | default |
| A-011 | Final answer | Explicit numeric/text answer or reference to a computed result with inherited conditions; unresolved graph does not override a best-effort answer | semantic | user |
| A-012 | Schema migration | Historical replies retain their original schema; do not pretend old outputs satisfy new work/binding schema | semantic | default |
| A-013 | Deployment status | Build prompts and offline replay only; paid readiness BLOCKED until natural new-schema output coverage and frozen batch/authorization | semantic | default |
| A-014 | Numeric metadata | Model declares subject/unit/period; explicit consumer binding asserts subject correspondence even if labels differ; unit/period strings must match, no host ontology or automatic conversion | semantic | default |
| A-015 | Schema resilience | Required core message/work list; each work item validated independently, optional malformed bindings isolated with notices; original raw retained | interface | default |
| A-016 | Revision propagation | Stable work IDs, owner-only revisions; preserve bindings for unchanged input definitions, including formula/conditions-only revisions; clear changed/removed input slots; changed output metadata blocks downstream stale bindings | interface | sweep |
| A-017 | First real engineering trace | Train task-05, literal table 1344.1 and paragraph 1137.4; manually authored total-minus-committed operation, explicitly engineering only | semantic | default |
| A-018 | Same-wave visibility | Build all member packets before processing a wave; reply admission uses that exact packet's source/work visibility | interface | default |
| A-019 | Historical replay coverage | First 12 full replies and original request schemas from local-rule-confirmation-live-20261025-r1; validate their old contracts and source IDs, explicitly expect incompatibility with new work schema | semantic | default |
| A-020 | CLI output independence | Checks use the task prepared in the requested --output directory, never silently reuse another preparation | interface | default |
| A-021 | Binding to provider revised within same wave | Reject when provider metadata differs from the consumer's saved snapshot; ID visibility alone is insufficient. Same-metadata value revisions may propagate normally | semantic | sweep |
| A-022 | Local repair granularity | Preserve unaffected input bindings across consumer revisions; do not require another model step merely for unchanged connections | interface | sweep |

## Notes

A-002 is an adapted information-complementarity setting, not native multi-agent TAT-QA or trained skill specialization. Full-context single-agent baseline retains all source access. A-003 selects for the declared research setting and must be disclosed; it is not a representative TAT-QA result. No scores will be computed from synthetic operations. The original dataset license is CC BY 4.0 per upstream README; attribution will be preserved in adapter metadata.

A-014 clarified before the binding-admission change: independent members may use different subject labels for the same quantity. Binding is the consumer's explicit semantic mapping, not a host string-alias guess. Unit/period conflicts remain blocked and visible; they may require a corrected provider declaration or a separate conversion operation. These mechanical checks do not certify declared metadata.

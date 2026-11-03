"""Real saved-response replay and offline v2 boundary/integration checks."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from coreta.closure import ClosureContracts, digest
from coreta.closure_format import FormatClosureClient, FormatClosureRunner
from coreta.schemas import ProtocolError
from coreta.state import reference_index
from coreta.task_audit_binding import (FactBindingSession, SourceBindingContracts, SourceBoundAuditRunner,
                                      bind_quote, source_registry)
from test_revision import TASK, candidate
from test_task_audit import AuditScript, audit
import test_task_audit as legacy_test
from tools.replay_source_bindings import migrate_legacy_for_binding, replay


ROOT = Path(__file__).resolve().parents[1]


def fact(key='f1', quote=TASK['prompt'], item_ids=('i1', 'i2'), source='prompt'):
    return {'fact_id': key, 'source_id': source, 'quoted_text': quote,
            'normalized_fact': 'Fixture interpretation', 'kind': 'constraint',
            'check_items': [{'item_id': item, 'description': 'Declared obligation ' + item} for item in item_ids]}


def incoming(*facts):
    return {'facts': list(facts or [fact()]), 'coverage_status': 'unknown'}


def item_audit(version=0, existing=None, observed='0', ids=('i1', 'i2')):
    result = audit(version, existing, observed)
    base = result['cases'][0]
    result['cases'] = [{**copy.deepcopy(base), 'case_id': f'c{n}', 'check_item_id': key,
                        'input': 'fixture-input-' + key} for n, key in enumerate(ids, 1)]
    result.update(check_item_ids=list(ids), coverage='all_declared_items')
    return result


class BindingScript(AuditScript):
    def __init__(self, mismatch=False, initial_bad=False, patch_bad=False):
        super().__init__(mismatch)
        self.initial_bad, self.patch_bad = initial_bad, patch_bad

    def __call__(self, payload, timeout):
        prompt = payload['instructions']
        context = json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]
        material = context['MATERIAL']
        props = payload['text']['format']['schema']['properties']
        if 'replacements' in props:
            self.seen.append(copy.deepcopy(context))
            value = {'replacements': [{'fact_id': f['fact_id'], 'source_id': 'prompt',
                                       'quoted_text': 'still absent' if self.patch_bad else material['task']['prompt']}
                                      for f in material['binding_feedback']['unresolved']]}
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps(value)}]}]}
        response = super().__call__(payload, timeout)
        value = json.loads(response['output'][0]['content'][0]['text'])
        if 'facts' in props:
            value = incoming(fact(quote='missing source quote' if self.initial_bad else material['task']['prompt']))
        elif 'candidate_hash' in props:
            original = value['audit_records'][0]
            value['audit_records'] = [item_audit(material['candidate_version'], original['existing_issue_id'],
                                                  '-3' if self.mismatch else '0')]
        response['output'][0]['content'][0]['text'] = json.dumps(value)
        return response


class SourceBindingChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.contracts = SourceBindingContracts(ROOT / 'design/v0.3/coreta.schema.json')
        self.config = json.loads((ROOT / 'config/deepseek_flash_closure.json').read_text(encoding='utf-8'))
        self.config['generation']['max_input_tokens'] = 1000000
        self.prompts = json.loads((ROOT / 'design/source_binding_prompts.json').read_text(encoding='utf-8'))

    def runner(self, script=None, path=None, bank=None):
        path = path or self.path
        path.mkdir(parents=True, exist_ok=True)
        runner = SourceBoundAuditRunner(TASK, path, 'binding-fixture', self.contracts, None,
                                        copy.deepcopy(self.config), self.prompts, draft_bank=bank)
        runner.client = FormatClosureClient(runner.config, runner.log, transport=script or BindingScript())
        return runner

    def prepared(self, ids=('i1', 'i2')):
        runner = self.runner()
        runner.version = 0
        runner.current = {'version': 0, 'source_event_id': 'binding-fixture:source', 'candidate': candidate()}
        session = FactBindingSession(TASK, incoming(fact(item_ids=ids)))
        runner.task_facts = runner.emit('task_facts', 'A2', session.bound_payload())
        runner._last_builder = 'A1'
        return runner

    def inspection(self, runner, ids=('i1', 'i2'), observed='0', existing=None):
        value = legacy_test.TaskAuditChecks.inspection(self, runner, observed, existing)
        value['audit_records'] = [item_audit(runner.version, existing, observed, ids)]
        return value

    def test_schema_has_no_model_offsets_and_preserves_initial_contract(self):
        Draft202012Validator.check_schema(self.contracts.document)
        properties = self.contracts.schema('TaskFacts')['properties']['facts']['items']['properties']
        self.assertNotIn('source_locator', properties)
        self.assertNotIn('source_binding', properties)
        old = ClosureContracts(ROOT / 'design/v0.3/coreta.schema.json')
        self.assertEqual(old.schema('Candidate'), self.contracts.schema('Candidate'))
        old_prompts = json.loads((ROOT / 'design/closure_prompts.json').read_text(encoding='utf-8'))
        for key in ('system', 'draft'):
            self.assertEqual(self.prompts[key], old_prompts[key])

    def test_exact_unicode_and_tex_no_whitespace_or_symbol_normalization(self):
        task = {**TASK, 'prompt': '甲😀乙\n$p(0,0) &= 0$'}
        registry = source_registry(task)
        location = bind_quote(registry, 'prompt', '😀乙\n$p(0,0) &= 0$')
        self.assertEqual(location['status'], 'unique_exact')
        self.assertEqual(location['start'], 1)
        self.assertEqual(task['prompt'][location['start']:location['end']], '😀乙\n$p(0,0) &= 0$')
        for changed in ('p(0,0) = 0', 'p(0,0)&=0', 'p(0,0) &=  0'):
            self.assertEqual(bind_quote(registry, 'prompt', changed)['status'], 'unmatched')

    def test_ambiguous_overlapping_and_short_quotes_do_not_choose_first(self):
        registry = source_registry({**TASK, 'prompt': 'aaaa X'})
        ambiguous = bind_quote(registry, 'prompt', 'aa')
        self.assertEqual(ambiguous['status'], 'ambiguous')
        self.assertEqual(ambiguous['match_count'], 3)
        self.assertNotIn('start', ambiguous)
        self.assertEqual(bind_quote(registry, 'prompt', '')['status'], 'unmatched')
        self.assertEqual(bind_quote(registry, 'prompt', 'a')['status'], 'ambiguous')
        self.assertEqual(bind_quote(registry, 'prompt', 'X')['status'], 'unique_exact')

    def test_registry_excludes_math_metadata_and_binds_code_entrypoint(self):
        self.assertEqual(set(source_registry(TASK)), {'prompt'})
        self.assertEqual(bind_quote(source_registry(TASK), 'entry_point', 'null')['status'], 'unknown_source')
        code = {**TASK, 'task_type': 'code', 'entry_point': 'public_function'}
        registry = source_registry(code)
        self.assertEqual(set(registry), {'prompt', 'entry_point'})
        bound = bind_quote(registry, 'entry_point', 'public_function')
        self.assertEqual(bound['public_field'], '/entry_point')
        self.assertEqual(bound['start'], 0)
        self.assertEqual(bind_quote(registry, '/MATERIAL/task/entry_point', 'public_function')['status'], 'unknown_source')

    def test_shared_source_does_not_delete_distinct_interpretations(self):
        one = fact('a', item_ids=('a1',))
        two = fact('b', item_ids=('b1',))
        two['normalized_fact'] = 'A distinct interpretation with the same exact quotation'
        session = FactBindingSession(TASK, incoming(one, two))
        self.assertEqual(len(session.bound_payload()['facts']), 2)
        self.assertEqual(session.bound_payload()['facts'][1]['semantic_status'], 'model_asserted')
        self.assertEqual(session.bound_payload()['coverage_status'], 'unknown')

    def test_collect_all_errors_patch_only_unresolved_and_lock_items(self):
        task = {**TASK, 'prompt': 'alpha beta red red'}
        one = fact('good', 'alpha', ('i1',))
        two = fact('missing', 'b eta', ('i2',))
        three = fact('repeat', 'red', ('i3',))
        session = FactBindingSession(task, incoming(one, two, three))
        self.assertEqual(session.pending, ['missing', 'repeat'])
        self.assertEqual(session.feedback()['locked_fact_ids'], ['good'])
        self.assertEqual([e['status'] for e in session.feedback()['unresolved']], ['unmatched', 'ambiguous'])
        session.apply_patch({'replacements': [
            {'fact_id': 'missing', 'source_id': 'prompt', 'quoted_text': 'beta'},
            {'fact_id': 'repeat', 'source_id': 'prompt', 'quoted_text': 'red red'}]})
        self.assertEqual(session.current['good'], one)
        self.assertEqual(session.current['missing']['check_items'], two['check_items'])
        self.assertEqual(session.current['missing']['normalized_fact'], two['normalized_fact'])
        self.assertEqual(session.pending, [])
        self.assertEqual(len(session.history), 2)

    def test_patch_cannot_change_locked_facts_drop_pending_or_repeat_ids(self):
        session = FactBindingSession(TASK, incoming(fact('good', item_ids=('i1',)), fact('bad', 'absent', ('i2',))))
        before = session.snapshot()
        for rows in ([], [{'fact_id': 'good', 'source_id': 'prompt', 'quoted_text': 'Compute'}],
                     [{'fact_id': 'bad', 'source_id': 'prompt', 'quoted_text': 'Compute'}] * 2):
            with self.assertRaises(ProtocolError):
                session.apply_patch({'replacements': rows})
            self.assertEqual(session.snapshot(), before)
        patch = {'replacements': [{'fact_id': 'bad', 'source_id': 'prompt', 'quoted_text': 'Compute',
                                   'check_items': []}]}
        with self.assertRaises(ProtocolError):
            self.contracts.validate('TaskFactsPatch', patch)

    def test_duplicate_fact_or_item_ids_rejected(self):
        for payload in (incoming(fact(), fact()),
                        incoming(fact('a', item_ids=('shared',)), fact('b', item_ids=('shared',)))):
            with self.assertRaises(ProtocolError):
                FactBindingSession(TASK, payload)

    def test_real_saved_responses_replay_without_fixing_offsets_or_quotes(self):
        result = replay()
        self.assertTrue(result['original_frozen_files_unchanged'])
        self.assertEqual([(r['bound_fact_count'], r['pending_fact_ids']) for r in result['attempts']],
                         [(9, ['F02']), (10, [])])
        self.assertTrue(result['incremental_repair']['locked_facts_unchanged'])
        self.assertEqual(result['incremental_repair']['final_bound_fact_count'], 10)
        self.assertFalse(result['legacy_atomicity_or_semantics_validated'])
        self.assertEqual(len(result['attempts'][0]['migration']['excluded']), 2)
        self.assertIn('source_locator', result['attempts'][0]['migration']['excluded'][0]['original_fact'])
        bound = result['incremental_repair']['bound_payload']['facts']
        # Quote repair cannot silently change an accepted interpretation from the first response.
        self.assertIn('real-coefficient', bound[0]['normalized_fact'])
        self.assertEqual(bound[0]['source_binding']['start'], 6)
        self.assertEqual(bound[0]['source_binding']['end'], 97)

    def test_unknown_legacy_pointer_prefix_is_not_silently_rewritten(self):
        old = {'facts': [{'fact_id': 'old', 'source_locator': {'kind': 'json_pointer', 'start': 0, 'end': 0,
                    'pointer': '/MATERIAL/task/entry_point'}, 'quoted_text': 'f', 'normalized_fact': 'entry',
                    'kind': 'domain'}]}
        payload, receipt = migrate_legacy_for_binding({**TASK, 'task_type': 'code', 'entry_point': 'f'}, old)
        self.assertEqual(payload['facts'], [])
        self.assertEqual(len(receipt['excluded']), 1)

    def test_one_case_cannot_claim_all_three_items_inside_one_fact(self):
        runner = self.prepared(('i1', 'i2', 'i3'))
        value = self.inspection(runner, ('i1',))
        self.contracts.validate('ClosureInspection', value)
        errors = runner._inspection_errors(value, 'A2', set(reference_index(runner.view())))
        self.assertTrue(any('all_declared_items' in e for e in errors))
        value['audit_records'][0]['coverage'] = 'sampled'
        self.assertEqual(runner._inspection_errors(value, 'A2', set(reference_index(runner.view()))), [])

    def test_all_items_require_individual_case_links_and_remain_model_assertions(self):
        runner = self.prepared(('i1', 'i2', 'i3'))
        value = self.inspection(runner, ('i1', 'i2', 'i3'))
        runner.settle(value, 'A2')
        self.assertEqual(runner.audit_ledger[-1]['validation_errors'], [])
        reports = [json.loads(x) for x in (runner.directory / 'item_coverage.jsonl').read_text().splitlines()]
        self.assertTrue(reports[0]['all_declared_items_mentioned'])
        self.assertFalse(reports[0]['task_exhaustiveness_proven'])
        self.assertEqual(reports[0]['semantic_status'], 'model_asserted')
        self.assertEqual(len(reports), 1)  # accept+settle must not duplicate coverage entries

    def test_unknown_wrong_parent_or_missing_item_case_blocks_closure(self):
        for problem in ('unknown', 'parent', 'missing'):
            runner = self.prepared()
            value = self.inspection(runner)
            if problem == 'unknown': value['audit_records'][0]['cases'][0]['check_item_id'] = 'unknown'
            if problem == 'parent': value['audit_records'][0]['cases'][0]['fact_id'] = 'unknown'
            if problem == 'missing': value['audit_records'][0]['cases'] = value['audit_records'][0]['cases'][:1]
            runner.settle(value, 'A2')
            self.assertTrue(runner.audit_ledger[-1]['validation_errors'])
            self.assertTrue(runner.blockers())

    def test_closure_rechecks_original_item_not_just_parent_fact_and_input(self):
        runner = self.prepared()
        value = self.inspection(runner, ('i1',), '-3')
        value['audit_records'][0]['coverage'] = 'sampled'
        runner.settle(value, 'A2')
        issue = runner.issues['i0001']
        runner.commit_proposals(legacy_test.TaskAuditChecks.update(self, runner, issue))
        wrong = self.inspection(runner, ('i2',), existing='i0001')
        wrong['audit_records'][0]['coverage'] = 'sampled'
        wrong['audit_records'][0]['cases'][0]['input'] = value['audit_records'][0]['cases'][0]['input']
        runner.settle(wrong, 'A2')
        self.assertEqual(runner.issues['i0001']['status'], 'open')
        self.assertTrue(any('check-item/input' in e for e in runner.audit_ledger[-1]['validation_errors']))

    def test_short_path_real_schema_and_task_only_visibility(self):
        script = BindingScript()
        runner = self.runner(script)
        result = runner.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['normal_calls'], 8)
        self.assertEqual(result['stop_reason'], 'complete')
        self.assertTrue(result['source_bindings_complete'])
        self.assertTrue(result['pipeline_completed'])
        self.assertTrue(result['mechanism_evaluable'])
        self.assertEqual(result['declared_check_item_count'], 2)
        self.assertEqual(set(script.seen[3]['MATERIAL']), {'task', 'source_registry'})
        self.assertFalse(any(e['stage'] == 'final' for e in runner.events))

    def test_targeted_binding_repair_is_one_logical_stage(self):
        script = BindingScript(initial_bad=True)
        runner = self.runner(script)
        result = runner.run()
        self.assertEqual(result['normal_calls'], 8)
        self.assertEqual(result['http_attempts'], 9)
        self.assertEqual(result['format_repairs'], 1)
        self.assertEqual(result['stop_reason'], 'complete')
        self.assertEqual(script.seen[4]['MATERIAL']['binding_feedback']['unresolved'][0]['fact_id'], 'f1')
        self.assertEqual(list(script.seen[4]['OUTPUT_SCHEMA']['properties']), ['replacements'])

    def test_malformed_initial_json_retries_initial_schema_and_retains_raw(self):
        outputs = ['{"facts":', json.dumps(incoming())]
        requests = []
        def transport(payload, timeout):
            requests.append(copy.deepcopy(payload))
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': outputs.pop(0)}]}]}
        runner = self.runner(transport)
        bound = runner.call('task_facts', 'A2', 'TaskFacts', {'task': TASK})
        self.assertEqual(bound['binding_status'], 'all_sources_bound')
        self.assertEqual(runner.calls, 1)
        self.assertEqual(runner.repairs, 1)
        self.assertEqual(runner.client.attempts, 2)
        self.assertTrue(all('facts' in p['text']['format']['schema']['properties'] for p in requests))
        raw_rows = [json.loads(x) for x in (runner.directory / 'responses.jsonl').read_text().splitlines()]
        self.assertEqual(raw_rows[0]['response']['output'][0]['content'][0]['text'], '{"facts":')

    def test_unresolved_after_budget_keeps_partial_state_and_original_facts(self):
        runner = self.runner(BindingScript(initial_bad=True, patch_bad=True))
        result = runner.run()
        self.assertEqual(result['status'], 'degraded')
        self.assertEqual(result['normal_calls'], 4)
        self.assertFalse(result['source_bindings_complete'])
        self.assertFalse(result['mechanism_evaluable'])
        state = json.loads((runner.directory / 'source_binding_state.json').read_text())
        self.assertEqual(state['pending_fact_ids'], ['f1'])
        self.assertEqual(len(state['current_facts']), 1)
        self.assertEqual(state['original_payload']['facts'][0]['quoted_text'], 'missing source quote')
        self.assertEqual(len(state['current_facts'][0]['check_items']), 2)

    def test_runner_repair_keeps_successful_fact_and_all_failed_condition_items(self):
        initial = incoming(fact('good', 'Compute', ('good-item',)), fact('bad', 'absent', ('bad-one', 'bad-two')))
        outputs = [initial, {'replacements': [{'fact_id': 'bad', 'source_id': 'prompt', 'quoted_text': TASK['prompt']}]}]
        requests = []
        def transport(payload, timeout):
            requests.append(copy.deepcopy(payload))
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps(outputs.pop(0))}]}]}
        runner = self.runner(transport)
        result = runner.call('task_facts', 'A2', 'TaskFacts', {'task': TASK})
        self.assertEqual(result['facts'][0]['quoted_text'], 'Compute')
        self.assertEqual(len(result['facts'][1]['check_items']), 2)
        self.assertEqual(runner.calls, 1)
        self.assertEqual(runner.client.attempts, 2)
        feedback_prompt = requests[1]['instructions']
        material = json.JSONDecoder().raw_decode(feedback_prompt[feedback_prompt.index('\n{"ACTOR"')+1:])[0]['MATERIAL']
        self.assertEqual(material['binding_feedback']['locked_fact_ids'], ['good'])
        self.assertEqual([f['fact_id'] for f in material['binding_feedback']['unresolved']], ['bad'])

    def test_full_rewrite_instead_of_patch_fails_without_losing_bound_facts(self):
        initial = incoming(fact('good', 'Compute', ('g',)), fact('bad', 'absent', ('b',)))
        outputs = [initial, incoming(fact('new', TASK['prompt'], ('new-item',)))]
        def transport(payload, timeout):
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps(outputs.pop(0))}]}]}
        runner = self.runner(transport)
        with self.assertRaises(ProtocolError):
            runner.call('task_facts', 'A2', 'TaskFacts', {'task': TASK})
        state = json.loads((runner.directory / 'source_binding_state.json').read_text())
        self.assertEqual(state['bindings']['good']['status'], 'unique_exact')
        self.assertEqual(state['pending_fact_ids'], ['bad'])
        self.assertEqual([f['fact_id'] for f in state['current_facts']], ['good', 'bad'])
        self.assertEqual(runner.client.attempts, 2)

    def test_worst_path_keeps_numeric_findings_and_fourteen_stage_budget(self):
        runner = self.runner(BindingScript(mismatch=True))
        result = runner.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['normal_calls'], 14)
        self.assertEqual(result['http_attempts'], 14)
        self.assertEqual(result['stop_reason'], 'budget_exhausted')
        self.assertEqual(result['audit_record_count'], 3)
        self.assertEqual(len(runner.issues['i0001']['evidence_records']), 3)
        self.assertEqual(runner.issues['i0001']['status'], 'open')
        self.assertEqual(runner.events[-1]['stage'], 'inspect')
        self.assertTrue(result['mechanism_evaluable'])

    def test_legacy_draft_bank_remains_compatible(self):
        bank = self.path / 'bank'
        old_dir = self.path / 'old'
        old_dir.mkdir()
        old_prompts = json.loads((ROOT / 'design/closure_prompts.json').read_text(encoding='utf-8'))
        old = FormatClosureRunner(TASK, old_dir, 'legacy', ClosureContracts(ROOT / 'design/v0.3/coreta.schema.json'),
                                  None, copy.deepcopy(self.config), old_prompts, draft_bank=bank)
        old.client = FormatClosureClient(old.config, old.log, transport=AuditScript())
        old.run_drafts()
        runner = self.runner(path=self.path / 'new', bank=bank)
        result = runner.run()
        self.assertEqual(result['normal_calls'], 8)
        self.assertEqual(result['http_attempts'], 5)
        self.assertEqual([e['payload'] for e in old.drafts], [e['payload'] for e in runner.drafts])


if __name__ == '__main__':
    unittest.main()

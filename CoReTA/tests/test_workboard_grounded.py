"""Offline transport fixtures; these checks measure execution, not model quality."""
import copy
import json
import unittest

import test_workboard as baseline
from coreta.handoff.gateway import Journal
from coreta.workboard.gateway import Gateway, defaults
from coreta.workboard.grounded import GroundRunner, GroundContracts, GroundPrompts
from coreta.schemas import ProtocolError


class GroundedTests(unittest.TestCase):
    setUp = baseline.WorkboardTests.setUp
    work = baseline.WorkboardTests.work
    change = baseline.WorkboardTests.change

    def respond(self, p):
        if p['STAGE'] == 'OBSERVE':
            value = baseline.WorkboardTests.offer(self, p)
            value['offer']['claims'] = [dict(statement='SCRIPTED claim', premises='SCRIPTED premises', source_refs=['T'])]
            return value
        if p['STAGE'] == 'GROUND':
            return dict(assessments={c['id']: dict(status='conflict', reason='SCRIPTED counterevidence', evidence_refs=['T'])
                                     for c in p['CLAIMS']}, limits='SCRIPTED not truth')
        return baseline.WorkboardTests.respond(self, p)

    def engine(self, handler=None, budget=19, total=100000):
        packets = copy.deepcopy(self.packets)
        packets.agents = packets.agents[:3]
        for member in packets.members.values():
            member['SELF']['team'] = packets.agents
        journal = Journal(self.folder)
        script = baseline.Script(journal, handler or self.respond)
        settings = defaults(3, self.legacy)
        settings['max_output_tokens']['ground'] = settings['max_output_tokens']['check_effect']
        settings['limits'].update(max_network_attempts_total=budget, max_output_tokens_total=total)
        gateway = Gateway(self.config, settings, GroundContracts(self.adapter), GroundPrompts(), journal,
                          transport=script, token_counter=lambda text: len(text)//3)
        return GroundRunner(packets, gateway, journal, self.adapter), script

    def test_full_order_and_budget(self):
        runner, script = self.engine()
        result = runner.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual([p['STAGE'] for p in script.calls], ['INITIAL']*3 +
            ['OBSERVE','OBSERVE','GROUND','TRY','CHECK_USE','CHOOSE']*2 +
            ['FINALIZE','FINAL_CHECK_USE','FINAL_CHECK_EFFECT','FINAL_CHOOSE'])
        self.assertEqual(result['http_attempts'],19)
        self.assertEqual(result['format_repairs'],0)
        self.assertEqual(result['method_variant'],'ground_full_public_v1')

    def test_review_reaches_try_without_automatic_veto(self):
        runner, script = self.engine()
        runner.run()
        for p in script.calls:
            if p['STAGE'] == 'TRY':
                r = p['GROUND_REVIEW']
                self.assertEqual(r['offer_ref'],p['TARGET_OFFER']['ref'])
                self.assertEqual(r['assessments']['C1']['status'],'conflict')
                self.assertEqual(r['assessments']['C1']['reason'],'SCRIPTED counterevidence')
        self.assertEqual(len(runner.checks),4)  # two ordinary + two final

    def test_ground_permissions_and_actual_diff(self):
        runner, script = self.engine()
        runner.run()
        for p in script.calls:
            member=p['SELF']['agent_id']
            self.assertEqual(p['SELF_MATERIALS'],runner.packets.member(member)['SELF_MATERIALS'])
            if p['STAGE']=='GROUND':
                self.assertNotIn(member,[runner.editor,p['TARGET_OFFER']['author']])
                self.assertNotIn('FEEDBACK',p)
                self.assertNotIn('CHECKS',p)
                self.assertEqual(p['PUBLIC_EVIDENCE'][-1]['base_version'],p['TARGET_OFFER']['base_version'])
                self.assertIn('proposed_use',p['TARGET_OFFER'])
                self.assertEqual(set(p['SOURCE_ACCESS']['direct_original_refs']),
                                 {'T',*(m['ref'] for m in p['SELF_MATERIALS'])})
            if p['STAGE']=='CHECK_USE':
                self.assertEqual(p['DIFF'],runner.board.diff(p['BEFORE']['id'],p['AFTER']['id']))
                self.assertEqual(p['USE_RECORD'],'SCRIPTED use description')

    def test_bad_ground_stops_without_retry(self):
        runner, script=self.engine(lambda p: 'NOT JSON' if p['STAGE']=='GROUND' else self.respond(p))
        result=runner.run()
        self.assertEqual(result['error']['code'],'SCHEMA_ERROR')
        self.assertEqual(result['http_attempts'],6)
        self.assertEqual(script.calls[-1]['STAGE'],'GROUND')
        self.assertFalse(result['closure_complete'])

    def test_identical_duplicate_target_is_audited_and_normalized(self):
        def duplicate_target(p):
            if p['STAGE'] != 'OBSERVE':
                return self.respond(p)
            target=json.dumps(p['CURRENT_WORK']['id'])
            claim=json.dumps(dict(statement='SCRIPTED claim', premises='SCRIPTED premises',
                                  source_refs=['T']))
            return ('{"action":"offer","offer":{"target":' + target +
                    ',"knowledge":"SCRIPTED knowledge","support":[{"ref":"T","excerpt":"SCRIPTED evidence"}]'
                    ',"proposed_use":"SCRIPTED use","claims":[' + claim + '],"target":' + target + '}}')
        runner,script=self.engine(duplicate_target)
        result=runner.run()
        self.assertEqual(result['status'],'completed')
        self.assertEqual(result['format_repairs'],4)
        repairs=(self.folder/'format_repairs.jsonl').read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(repairs),4)
        self.assertTrue(all(json.loads(row)['kind']=='identical_duplicate_keys_collapsed' for row in repairs))
        stage_rows=[json.loads(row) for row in (self.folder/'stages.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual([row['repair'] for row in stage_rows if row['stage']=='OBSERVE'],[1,1,1,1])

    def test_conflicting_duplicate_target_still_fails(self):
        def duplicate_target(p):
            if p['STAGE'] != 'OBSERVE':
                return self.respond(p)
            a=json.dumps(p['CURRENT_WORK']['id']);b=json.dumps('different-target')
            return ('{"action":"offer","offer":{"target":' + a+
                    ',"knowledge":"SCRIPTED knowledge","support":[{"ref":"T","excerpt":"SCRIPTED evidence"}]'
                    ',"proposed_use":"SCRIPTED use","claims":[{"statement":"c","premises":"p","source_refs":["T"]}]'
                    ',"target":' + b + '}}')
        runner,script=self.engine(duplicate_target)
        result=runner.run()
        self.assertEqual(result['error']['code'],'SCHEMA_ERROR')
        self.assertEqual(result['http_attempts'],4)
        self.assertEqual(len(script.calls),4)
        self.assertFalse((self.folder/'format_repairs.jsonl').exists())

    def test_identical_duplicate_is_audited_even_if_schema_later_fails(self):
        def duplicate_but_incomplete(p):
            if p['STAGE'] != 'OBSERVE':
                return self.respond(p)
            target=json.dumps(p['CURRENT_WORK']['id'])
            return ('{"action":"offer","offer":{"target":' + target+
                    ',"knowledge":"SCRIPTED knowledge","support":[],'
                    '"proposed_use":"SCRIPTED use","target":' + target + '}}')
        runner,_=self.engine(duplicate_but_incomplete)
        result=runner.run()
        self.assertEqual(result['error']['code'],'SCHEMA_ERROR')
        self.assertEqual(result['format_repairs'],1)
        repair=json.loads((self.folder/'format_repairs.jsonl').read_text(encoding='utf-8').splitlines()[0])
        self.assertEqual(repair['keys'],['target'])
        error=json.loads((self.folder/'stage_errors.jsonl').read_text(encoding='utf-8').splitlines()[0])
        self.assertEqual(error['repair'],1)

    def test_missing_claim_result_rejected(self):
        runner, _=self.engine(lambda p: dict(assessments={},limits='fixture') if p['STAGE']=='GROUND' else self.respond(p))
        self.assertEqual(runner.run()['error']['code'],'SCHEMA_ERROR')

    def test_inaccessible_original_citation_rejected(self):
        def handler(p):
            value=self.respond(p)
            if p['STAGE']=='GROUND':
                value['assessments']['C1']['evidence_refs']=['S999999']
            return value
        runner,_=self.engine(handler)
        self.assertEqual(runner.run()['error']['code'],'SCHEMA_ERROR')

    def test_reserve_closure_under_small_budget(self):
        runner,script=self.engine(budget=12)
        result=runner.run()
        self.assertEqual(result['status'],'completed')
        self.assertEqual(len(script.calls),7)
        self.assertNotIn('GROUND',[p['STAGE'] for p in script.calls])

    def test_output_budget_blocks_request(self):
        runner,script=self.engine(total=1)
        result=runner.run()
        self.assertEqual(result['error']['code'],'OUTPUT_BUDGET')
        self.assertEqual(len(script.calls),0)

    def test_pass_and_unable_paths(self):
        runner,script=self.engine(lambda p: dict(action='pass',offer=None) if p['STAGE']=='OBSERVE' else self.respond(p))
        self.assertEqual(runner.run()['status'],'completed')
        self.assertNotIn('GROUND',[p['STAGE'] for p in script.calls])

    def test_unable_after_ground_skips_application_check(self):
        runner,script=self.engine(lambda p: self.change('unable') if p['STAGE']=='TRY' else self.respond(p))
        self.assertEqual(runner.run()['status'],'completed')
        self.assertEqual(sum(p['STAGE']=='GROUND' for p in script.calls),2)
        self.assertNotIn('CHECK_USE',[p['STAGE'] for p in script.calls])

    def test_missing_output_cap_rejected(self):
        runner,_=self.engine()
        del runner.gateway.outputs['ground']
        with self.assertRaises(ProtocolError):
            GroundRunner(runner.packets,runner.gateway,runner.journal,self.adapter)


if __name__=='__main__':
    unittest.main()


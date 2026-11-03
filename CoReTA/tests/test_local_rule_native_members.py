import unittest
import tempfile
from pathlib import Path
import json
import audit_existing_task_fit_20261025 as audit
import local_judgment_frontend as io
import local_rule_frontend as frontend
import local_rule_team_integration as team
import prepare_local_rule_adoption as old

class NativeMembersTests(unittest.TestCase):
    def test_fourth_member_is_usable_and_unshared_originals_stay_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);audit.build(root/'audit',root/'pack')
            folder=root/'pack/hb-local-dev-009/packets/distributed'
            packets=[io.read(folder/f'A{i}.json') for i in range(1,5)]
            draft=dict(draft_id='W0',artifact=None,reason='Technical draft fixture, not experimental data.',claims=[dict(id='D1',text='Technical fixture.')])
            fourth=dict(packets[3],historical_work=draft)
            req=frontend.request('first','local_question',fourth)
            self.assertIn('A4.S1',req['schema']['properties']['source_ids']['items']['enum'])
            decoded=frontend.decode_first(json.dumps(dict(text='Technical local question.',status='proceed',source_ids=['A4.S1'],target_ids=['D1'])),fourth)
            second=frontend.second_packet(fourth,decoded)
            self.assertNotIn('historical_work',second)
            self.assertEqual(second['member'],'A4')
            deliveries={}
            for packet in packets:
                deliveries[packet['member']]=dict(conclusion='Technical fixture.',status='conditional',scope='Fixture.',missing=[],
                    evidence=[] if packet['member']=='A3' else [dict(source=packet['own_sources'][0]['ref'],quote=packet['own_sources'][0]['content'])])
            shared=team.assemble(packets[0]['task'],packets[0]['public_sources'],draft,packets,deliveries)
            refs={s['ref'] for s in shared['disclosed_evidence']}
            self.assertIn('A4.S1',refs);self.assertNotIn('A3.S1',refs)
            self.assertEqual(team.request(shared)['instructions'],old.INSTRUCTIONS+'\nPACKET='+json.dumps(shared,ensure_ascii=False))
            self.assertEqual(team.schema(shared)['properties']['used_contributions']['items']['enum'],['C1','C2','C3','C4'])
            out=team.decode(json.dumps(dict(choice='O1',reasoning='Technical fixture.',used_contributions=['C4'])),shared)
            self.assertEqual(out['used_contributions'],['C4']);self.assertEqual(out['annotation_issues'],[])
            deliveries['A1']['evidence']=[dict(source='A4.S1',quote=packets[3]['own_sources'][0]['content'])]
            with self.assertRaisesRegex(ValueError,'visible'):team.assemble(packets[0]['task'],packets[0]['public_sources'],draft,packets,deliveries)

    def test_three_member_historical_decoder_remains_identical(self):
        prepared=io.ROOT/'runs/local-rule-adoption-prepared-20261025-r2'
        history=io.ROOT/'runs/local-rule-adoption-live-20261025-r1'
        for row in io.read(prepared/'PLAN.json')['schedule']:
            packet=io.read(prepared/row['packet']);raw=(history/f"{row['slot']:02d}.raw.txt").read_text(encoding='utf-8')
            self.assertEqual(team.request(packet),old.request(packet))
            self.assertEqual(team.decode(raw,packet),old.decode(raw,packet))

if __name__=='__main__':unittest.main()

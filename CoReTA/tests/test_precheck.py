import json
import tempfile
import unittest
from pathlib import Path
from coreta.closure import ClosureClient, ClosureContracts
from coreta.precheck import PrecheckRunner
from test_closure import ClosureScript, proposal
from test_revision import TASK

ROOT = Path(__file__).resolve().parents[1]


class PrecheckScript(ClosureScript):
    def __call__(self, payload, timeout):
        props = payload['text']['format']['schema']['properties']
        if 'checks' not in props or 'candidate_hash' in props:
            return super().__call__(payload, timeout)
        instructions = payload['instructions']
        c = json.JSONDecoder().raw_decode(instructions[instructions.index('\n{"ACTOR"')+1:])[0]
        self.seen.append(c)
        value = {'checks': [{'target_refs': [c['REFERENCE_INDEX'][0]], 'method': 'manual',
            'observation': 'One plus one equals two', 'conclusion': 'supported', 'scope': 'addition'}],
            'issues': [proposal('i0001')] if self.reject else []}
        return {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(value)}]}]}


class PrecheckChecks(unittest.TestCase):
    def runner(self, reject=False):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        cfg = json.loads((ROOT/'config/deepseek_flash_closure.json').read_text(encoding='utf-8'))
        cfg['generation']['max_input_tokens'] = 1000000
        prompts = json.loads((ROOT/'design/precheck_prompts.json').read_text(encoding='utf-8'))
        script = PrecheckScript(reject=reject)
        r = PrecheckRunner(TASK, Path(tmp.name), 'control', ClosureContracts(ROOT/'design/v0.3/coreta.schema.json'),
            None, cfg, prompts)
        r.client = ClosureClient(cfg, r.log, transport=script)
        return r, script

    def test_sequence_and_direct_export(self):
        r, _ = self.runner(); result = r.run()
        self.assertEqual([e['stage'] for e in r.events][-3:], ['build', 'inspect', 'apply'])
        self.assertEqual(result['stop_reason'], 'complete')
        self.assertEqual(result['normal_calls'], 7)
        self.assertEqual(result['review_status'], 'unreviewed')
        self.assertEqual(result['artifact'], result['delivery_candidate']['candidate']['artifact'])

    def test_lead_can_close_despite_precheck_objection(self):
        r, _ = self.runner(reject=True); result = r.run()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['stop_reason'], 'complete')
        self.assertEqual(result['issues']['i0001']['status'], 'addressed')
        self.assertEqual(len(result['issues']['i0001']['objections']), 2)

    def test_initial_generation_inputs_match_postcheck(self):
        r, _ = self.runner()
        post = json.loads((ROOT/'design/closure_prompts.json').read_text(encoding='utf-8'))
        self.assertEqual(r.prompts['system'], post['system'])
        self.assertEqual(r.prompts['draft'], post['draft'])
        self.assertEqual(r.config['generation']['max_output_tokens']['inspect'], 4096)


if __name__ == '__main__': unittest.main()

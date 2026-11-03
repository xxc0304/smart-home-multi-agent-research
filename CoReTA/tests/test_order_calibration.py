import json
from pathlib import Path
import tempfile
import unittest
from order_calibration import ROOT, prepare, run


class CalibrationTests(unittest.TestCase):
    def test_mock_without_task_pack_access_and_invalid_order_not_format_error(self):
        pack=ROOT/'runs/distributed-order-tasks-prepared-20261024-r1'
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prepare(pack,root/'prepared')
            calls=[]
            def transport(payload,timeout):
                calls.append(payload)
                schema=payload['text']['format']['schema']
                self.assertEqual(list(schema['properties']),['reason','order'])
                self.assertNotIn('maxLength',schema['properties']['reason'])
                self.assertIn('order LAST',payload['instructions'])
                order=['J1']*schema['properties']['order']['minItems']
                return dict(status='completed',usage=dict(input_tokens=100,output_tokens=30),
                    output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(dict(order=order,reason='Mock only. '*200)))])])
            result=run(root/'prepared',root/'run',transport=transport)
            self.assertEqual(result['attempts'],12)
            self.assertEqual(result['status'],'completed')
            for payload in calls:
                packet=json.loads(payload['instructions'].split('PACKET=',1)[1])
                self.assertEqual(set(packet),{'task','source_sheets'})
                self.assertEqual(len(packet['source_sheets']),3)
                self.assertTrue(packet['task']['id'].startswith('calibration-'))


if __name__=='__main__': unittest.main()

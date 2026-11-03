import json
from pathlib import Path
import tempfile
import unittest
from order_feedback_pilot import prepare,run,read


class FeedbackTests(unittest.TestCase):
    def test_pairs_equal_except_feedback_and_labels_not_read_live(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';prepare(p);m=read(p/'manifest.json')
            self.assertEqual(m['preflight']['initial_correct'],5)
            groups={}
            for row in m['schedule']:
                request=read(p/row['request'])
                packet=json.loads(request['instructions'].split('PACKET=',1)[1])
                packet.pop('execution_feedback')
                groups.setdefault(row['unit'],[]).append(packet)
            self.assertTrue(all(a==b for a,b in groups.values()))
            (p/'offline_initial_labels.json').unlink()
            def mock(payload,timeout):
                packet=json.loads(payload['instructions'].split('PACKET=',1)[1])
                answer=dict(reason='Mock only. '*200,order=packet['initial']['order'])
                return dict(status='completed',usage=dict(input_tokens=100,output_tokens=40),
                    output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])
            state=run(p,root/'run',transport=mock)
            self.assertEqual(state['attempts'],26)
            self.assertEqual(state['status'],'completed')


if __name__=='__main__':unittest.main()

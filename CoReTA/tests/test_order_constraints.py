import unittest
from coreta.workboard.order_constraints import solutions, violations


class OrderTests(unittest.TestCase):
    def test_time_boundary_and_precedence(self):
        jobs = {'A': {'duration': 3}, 'B': {'duration': 2}}
        rules = [dict(id='d', op='deadline', a='A', value=3),
                 dict(id='p', op='before', a='A', b='B')]
        self.assertEqual(solutions(jobs,rules), [['A','B']])
        self.assertEqual(violations(['B','A'],jobs,rules), ['d','p'])

    def test_no_duplicate_or_omitted_jobs(self):
        with self.assertRaises(ValueError):
            violations(['A','A'], {'A':{},'B':{}}, [])

    def test_adjacency_and_one_based_positions(self):
        jobs = {k:{'duration':1} for k in 'ABC'}
        rules = [dict(id='n',op='not_adjacent',a='A',b='B'),
                 dict(id='x',op='not_position',a='C',value=2)]
        self.assertEqual(solutions(jobs,rules), [])


if __name__ == '__main__':
    unittest.main()

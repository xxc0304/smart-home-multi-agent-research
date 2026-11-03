import unittest
from coreta.workboard.local_conditions import Condition, ConditionBoard


class LocalConditionsTests(unittest.TestCase):
    def setUp(self):
        self.board = ConditionBoard({"a": {"age": 53}, "b": {"age": 17}, "c": {}},
                                    {"task": "Choose someone under 30.",
                                     "member": "The two people travelled together."})
        self.board.add(Condition("age", "age", "lt", 30, "task_requirement",
                                 "task", "under 30"))

    def test_correct_requirement_changes_eligible_submission(self):
        with self.assertRaises(ValueError):
            self.board.submit("a", 1, {"age": "I acknowledge it"})
        self.assertEqual(self.board.submit("b", 1)["status"],
                         "consistent_with_encoded_conditions")

    def test_false_member_interpretation_is_visible_not_hard_veto(self):
        self.board.add(Condition("false", "age", "gt", 40, "member_interpretation",
                                 "member", "travelled together"))
        with self.assertRaises(ValueError):
            self.board.submit("b", 2)
        result = self.board.submit("b", 2, {"false": "Source does not establish age."})
        self.assertEqual(result["status"], "unresolved")
        self.board.revise("false", None, "Age was inferred without support.",
                          "member", "travelled together")
        self.assertEqual(self.board.submit("b", 3)["status"],
                         "consistent_with_encoded_conditions")
        self.assertIn("b", self.board.candidates)
        self.assertEqual(self.board.history[-1]["before"]["b"]["checks"][-1]["status"], "violates")

    def test_unknown_and_budget_fallback_never_pass(self):
        self.assertEqual(self.board.submit("c", 1, {"age": "Age unavailable."})["status"], "unresolved")
        self.assertEqual(self.board.submit("a", 1, {"age": "Budget exhausted."}, True)["status"], "unresolved")

    def test_revision_invalidates_previous_checks(self):
        self.board.revise("age", None, "Diagnostic withdrawal.", "task", "under 30")
        with self.assertRaises(ValueError):
            self.board.submit("b", 1)

    def test_invalid_quote_or_revision_rejected(self):
        with self.assertRaises(ValueError):
            self.board.add(Condition("bad", "age", "lt", 30, "member_interpretation", "task", "invented"))
        with self.assertRaises(ValueError):
            self.board.revise("age", None, "", "task", "under 30")


if __name__ == "__main__":
    unittest.main()

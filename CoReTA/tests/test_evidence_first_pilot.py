import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import evidence_first_frontend as frontend
import run_evidence_first_pilot as runner
import export_evidence_first_pilot as scorer


class EvidenceFirstTests(unittest.TestCase):
    @staticmethod
    def response(payload,call=1):
        packet=json.loads(payload["instructions"].split("PACKET=",1)[1])
        if "contributions" in packet:
            value=dict(choice="O1",reasoning="Technical integration fixture.",used_contributions=["C4"])
        elif "earlier_work" in packet:
            value=dict(conclusion="Newly noticed local evidence.",status="conditional",
                       source_ids=[packet["member"]+".S1"],scope="A local test finding.",missing=[])
        else:
            value=dict(text=f"First-view technical finding {call}.",status="proceed",source_ids=[])
        return dict(status="completed",error=None,usage=dict(input_tokens=10,output_tokens=10),
                    output=[dict(type="message",content=[dict(type="output_text",text=json.dumps(value))])])

    def test_complete_dataflow_privacy_and_all_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,o=Path(tmp)/"p",Path(tmp)/"o";runner.freeze(p);original=io.read;calls=0
            def guard(path):
                self.assertNotIn("OFFLINE_",str(path))
                return original(path)
            def mock(payload,timeout):
                nonlocal calls
                calls+=1
                Draft202012Validator.check_schema(payload["text"]["format"]["schema"])
                return self.response(payload,calls)
            with patch.object(io,"read",guard):
                state=runner.run(p,o,transport=mock,local_validation=True)
            self.assertEqual((state["attempts"],state["status"]),(72,"completed"))
            self.assertEqual(len(list(o.glob("*.raw.txt"))),72)
            rows={r["slot"]:r for r in state["rows"]}
            for row in runner.schedule():
                req=original(o/"actual_requests"/f"{row['slot']:03d}.json")
                packet=json.loads(req["instructions"].split("PACKET=",1)[1])
                self.assertEqual(set(req["schema"]["required"]),set(req["schema"]["properties"]))
                if row["stage"]=="integrate":
                    self.assertEqual([c["id"] for c in packet["contributions"]],["C1","C2","C3","C4"])
                    self.assertEqual(len([s for s in packet["disclosed_evidence"] if s["ref"].startswith("A")]),4)
                    continue
                self.assertEqual([s["ref"] for s in packet["own_sources"]],[row["member"]+".S1"])
                has_draft=(row["method"]=="ordinary")==(row["stage"]=="first")
                self.assertEqual("historical_work" in packet,has_draft)
                if has_draft:
                    self.assertEqual(packet["historical_work"],original(p/"drafts"/row["task"]/f"r{row['repeat']}.json"))
                if row["stage"]=="second":
                    self.assertEqual(packet["earlier_work"],rows[row["slot"]-1]["answer"]["text"])
                    # First disclosed no sources; second may freely use an original.
                    self.assertEqual(rows[row["slot"]-1]["answer"]["evidence"],[])
                    self.assertTrue(rows[row["slot"]]["answer"]["evidence"])
            with self.assertRaisesRegex(ValueError,"no resume"):
                runner.run(p,o,transport=mock,local_validation=True)

    def test_pass_continues_second_view_and_is_not_a_whitelist(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,o=Path(tmp)/"p",Path(tmp)/"o";runner.freeze(p);calls=0
            def mock(payload,timeout):
                nonlocal calls
                calls+=1;r=self.response(payload,calls)
                packet=json.loads(payload["instructions"].split("PACKET=",1)[1])
                if "contributions" not in packet and "earlier_work" not in packet:
                    value=json.loads(r["output"][0]["content"][0]["text"]);value["status"]="pass"
                    r["output"][0]["content"][0]["text"]=json.dumps(value)
                return r
            result=runner.run(p,o,transport=mock,local_validation=True)
            self.assertEqual(result["attempts"],72)
            self.assertTrue(all(r["status"]=="readable" for r in result["rows"]))
            self.assertTrue(all(r["answer"]["status"]=="pass" for r in result["rows"] if r["stage"]=="first"))
            self.assertTrue(all(r["answer"]["evidence"] for r in result["rows"] if r["stage"]=="second"))

    def test_strict_contract_rejects_missing_fields_types_sources_and_extra_json(self):
        packet=io.read(runner.DATA/runner.TASKS[0]/"packets/distributed/A1.json")
        samples={
            "first":dict(text="A local finding.",status="proceed",source_ids=["A1.S1"]),
            "second":dict(conclusion="A local result.",status="conditional",source_ids=["A1.S1"],scope="Local.",missing=[]),
        }
        for stage,value in samples.items():
            self.assertTrue(frontend.decode(json.dumps(value),stage,packet))
            for field in value:
                broken=copy.deepcopy(value);broken.pop(field)
                with self.subTest(stage=stage,missing=field),self.assertRaises(ValueError):
                    frontend.decode(json.dumps(broken),stage,packet)
            broken=dict(value,source_ids=["A2.S1"])
            with self.assertRaises(ValueError):frontend.decode(json.dumps(broken),stage,packet)
            for altered in (dict(value,source_ids=None),dict(value,source_ids="A1.S1"),dict(value,extra="x")):
                with self.assertRaises(ValueError):frontend.decode(json.dumps(altered),stage,packet)
            with self.assertRaises(ValueError):frontend.decode(json.dumps(value)+"{}",stage,packet)
            with self.assertRaises(ValueError):frontend.decode('{"text":"a","text":"b"}',stage,packet)
        packet=dict(task=packet["task"],contributions=[dict(id="C1")])
        for value in (dict(choice="O1",reasoning="Reason."),dict(reasoning="Reason.",used_contributions=[]),
                      dict(choice="bad",reasoning="Reason.",used_contributions=[]),
                      dict(choice="O1",reasoning="Reason.",used_contributions=["C2"])):
            with self.assertRaises(ValueError):frontend.decode_integration(json.dumps(value),packet)
        self.assertIsNone(frontend.decode_integration(json.dumps(dict(choice=None,reasoning="Unresolved.",used_contributions=[])),packet)["choice"])

    def test_bad_branch_isolated_and_complete_roster_preserved(self):
        for badslot in (1,2,9):
            with self.subTest(badslot=badslot),tempfile.TemporaryDirectory() as tmp:
                p,o=Path(tmp)/"p",Path(tmp)/"o";runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1;r=self.response(payload,calls)
                    if calls==badslot:
                        value=json.loads(r["output"][0]["content"][0]["text"])
                        value.pop("used_contributions" if badslot==9 else "source_ids")
                        r["output"][0]["content"][0]["text"]=json.dumps(value)
                    return r
                result=runner.run(p,o,transport=mock,local_validation=True)
                rows=io.read(o/"review.json")["rows"]
                self.assertEqual(len(rows),72)
                self.assertEqual(rows[badslot-1]["status"],"quarantined")
                if badslot==1:
                    self.assertEqual(rows[1]["status"],"blocked_upstream")
                if badslot in (1,2):
                    self.assertEqual(rows[8]["status"],"blocked_upstream")
                self.assertEqual(rows[17]["status"],"readable")  # other method unaffected
                self.assertEqual(result["status"],"completed_with_quarantine")

    def test_systemic_faults_and_budgets_stop_without_retry(self):
        for mode in ("two_bad","transport","usage","overcap","input"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                p,o=Path(tmp)/"p",Path(tmp)/"o";runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if mode=="transport" and calls==2:raise TimeoutError("Fixture")
                    r=self.response(payload,calls)
                    if mode=="two_bad":r["output"][0]["content"][0]["text"]="{"
                    if mode=="usage" and calls==2:r.pop("usage")
                    if mode=="overcap" and calls==2:r["usage"]["output_tokens"]=1537
                    if mode=="input" and calls==2:r["usage"]["input_tokens"]=runner.INPUT_CAP+1
                    return r
                with self.assertRaises((RuntimeError,ProtocolError)):
                    runner.run(p,o,transport=mock,local_validation=True)
                self.assertEqual(calls,2)
                self.assertEqual(io.read(o/"progress.json")["status"],"stopped")
                self.assertEqual(len(io.read(o/"review.json")["rows"]),72)
        with tempfile.TemporaryDirectory() as tmp:
            p,o=Path(tmp)/"p",Path(tmp)/"o";runner.freeze(p)
            with patch.object(DeepSeekClient,"size",return_value=runner.INPUT_CAP+1):
                with self.assertRaisesRegex(RuntimeError,"pre-request"):
                    runner.run(p,o,transport=self.response,local_validation=True)
            self.assertEqual(io.read(o/"progress.json")["attempts"],0)

    def test_real_history_replay_and_wrong_authorization_or_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"p";runner.freeze(p)
            report=runner.preflight(p)
            self.assertEqual(report["replay_requests"],72)
            self.assertLess(report["maximum_input_estimate"],32768)
            self.assertLess(report["total_input_estimate"],runner.INPUT_CAP)
            sha=io.digest(p/"manifest.json")
            io.write(p/"EXPERIMENT_REVIEW.json",dict(science="PASS",readiness="PASS",technical_launch="RUN_ALLOWED",manifest_sha256=sha))
            auth=dict(authorized=True,max_requests=72,max_output_tokens=110592,max_input_tokens=393216,
                      destination="https://api.deepseek.com/responses",manifest_sha256=sha,user_authorization_text="TEST ONLY")
            io.write(p/"AUTHORIZATION.json",auth);runner.gates(p)
            io.write(p/"AUTHORIZATION.json",dict(auth,max_requests=152))
            with self.assertRaisesRegex(ValueError,"authorization"):runner.gates(p)
            (p/"drafts"/runner.TASKS[0]/"r1.json").write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"changed"):runner.verify(p)

    def test_partial_export_marks_unknown_and_fixtures_not_live_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,o=Path(tmp)/"p",Path(tmp)/"o";runner.freeze(p)
            calls=0
            def mock(payload,timeout):
                nonlocal calls
                calls+=1
                if calls==10:
                    raise TimeoutError("Interruption fixture")
                return self.response(payload,calls)
            with self.assertRaises(ProtocolError):
                runner.run(p,o,transport=mock,local_validation=True)
            report=scorer.export(p,o)
            self.assertEqual(report["scope"],"TECHNICAL_FIXTURE_NOT_EXPERIMENTAL_RESULTS")
            self.assertEqual(report["paid_live_requests"],0)
            self.assertEqual(len(report["finals"]),8)
            unknown=[r for r in report["finals"] if r["outcome"]=="technical_unknown"]
            self.assertEqual(len(unknown),7)
            self.assertTrue(all(r["reference_match"] is None and r["choice"] is None for r in unknown))
            self.assertEqual(report["by_method"]["evidence_first"]["technical_unknown"],4)


if __name__=="__main__":
    unittest.main()

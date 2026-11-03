"""Offline follow-up checks; scripted outputs are not research results."""
import importlib.util
import json
import unittest
from pathlib import Path

import test_workboard as fixtures
from coreta.handoff.__main__ import PROJECT
from coreta.schemas import ProtocolError

spec = importlib.util.spec_from_file_location("followup", PROJECT / "tools/workboard_followup.py")
followup = importlib.util.module_from_spec(spec); spec.loader.exec_module(followup)


class FollowupTests(unittest.TestCase):
    setUp = fixtures.WorkboardTests.setUp
    work = fixtures.WorkboardTests.work
    change = fixtures.WorkboardTests.change
    offer = fixtures.WorkboardTests.offer
    respond = fixtures.WorkboardTests.respond

    def source_packet(self):
        row = json.loads(followup.TRANSCRIPT.read_text(encoding="utf-8").splitlines()[6])
        return json.loads(row["payload"]["instructions"].split("\nPACKET=", 1)[1].split("\nOUTPUT_SCHEMA=", 1)[0])

    def factory(self, row):
        def handler(p):
            if p["STAGE"] == "DISCUSS": return self.work()
            if p["STAGE"] == "OBSERVE": return self.offer(p)
            return self.respond(p)
        return fixtures.Script(None, handler)

    def test_marker_changes_no_fact_source_or_access(self):
        original = self.source_packet(); marked = followup.variant(original, True)
        self.assertNotIn("SOURCE_DECLARATION_NOTE", original)
        for key in original:
            if key != "CANDIDATES": self.assertEqual(marked[key], original[key])
        for a,b in zip(original["CANDIDATES"], marked["CANDIDATES"]):
            self.assertEqual(a, {k:v for k,v in b.items() if k != "source_declaration_status"})
            self.assertEqual(b["declared_sources"], [])

    def test_historical_cache_preserves_substantive_fixture_fields(self):
        from coreta.application_v2.inputs import Packets
        packets = Packets(followup.pilot.PACK, "concentrated_A1")
        cache = followup.historical_cache(packets)
        f = next(x for x in followup.read(followup.HISTORY)["fixtures"] if x["fixture_id"] == "derived_error")
        for record in f["contributions"]:
            work = cache["candidates"][record["author"]]
            self.assertIn(record["content"], work["work_text"])
            self.assertIn(record["support"], work["work_text"])
            self.assertIn(json.dumps(record["support_refs"], ensure_ascii=False), work["work_text"])
            self.assertNotIn("derived_error", work["work_text"])
        self.assertIsNone(cache["candidates"]["A1"]["artifact"])
        self.assertIn("private subtotal=-5", cache["candidates"]["A1"]["work_text"])
        self.assertIn("Reported shared subtotal=-1", cache["candidates"]["A1"]["work_text"])

    def test_preparation_freezes_eight_exact_or_marked_probes(self):
        out=self.folder/'prepared'; m=followup.prepare(out)
        self.assertEqual(len(m["probes"]), 8)
        self.assertEqual(m["max_http_attempts"], 108)
        self.assertEqual(sum(p["variant"]=='original' for p in m['probes']), 4)
        self.assertEqual({p['stage'] for p in m['probes']}, {'DISCUSS','FINALIZE'})

    def test_full_scripted_diagnostics_use_108_calls_and_shared_inputs(self):
        prepared=self.folder/'prepared'; out=self.folder/'run'; followup.prepare(prepared)
        r=followup.run(prepared,out,transport_factory=self.factory)
        self.assertEqual(r['status'],'completed');self.assertEqual(r['http_attempts'],108)
        for pair in ('historical-r1','historical-r2'):
            states=[followup.read(out/pair/m/'state.json') for m in ('ordinary_discussion','coreta_workboard')]
            self.assertEqual([w for w in states[0]['works'] if w['initial']],
                             [w for w in states[1]['works'] if w['initial']])

    def test_first_probe_format_error_stops_everything(self):
        prepared=self.folder/'prepared';out=self.folder/'run';followup.prepare(prepared)
        with self.assertRaises(ProtocolError):
            followup.run(prepared,out,transport_factory=lambda _: fixtures.Script(None,lambda _: 'NOT JSON'))
        r=followup.read(out/'progress.json')
        self.assertEqual(r['status'],'stopped_on_first_technical_error')
        self.assertEqual(r['http_attempts'],1)
        self.assertTrue(all(u['status']=='not_started' for u in r['units']))

    def test_changed_input_rejected_before_execution(self):
        prepared=self.folder/'prepared';out=self.folder/'run';m=followup.prepare(prepared)
        (prepared/(m['probes'][0]['id']+'.json')).write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):followup.run(prepared,out,transport_factory=self.factory)
        self.assertFalse(out.exists())

    def test_standalone_history_does_not_rerun_probes(self):
        prepared=self.folder/'prepared';out=self.folder/'run'
        m=followup.prepare(prepared,historical_only=True)
        self.assertEqual(m['probes'],[]);self.assertEqual(m['max_http_attempts'],100)
        r=followup.run(prepared,out,transport_factory=self.factory)
        self.assertEqual(r['http_attempts'],100);self.assertEqual(r['status'],'completed')
        self.assertEqual(r['probes'],[])


if __name__=='__main__':unittest.main()

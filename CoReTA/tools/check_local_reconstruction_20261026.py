"""Network-free lineage, visibility, real-output replay and boundary checks."""
import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from tokenizers import Tokenizer

import local_judgment_frontend as io
import local_reconstruction_probe as probe
import minimal_final_answer_contract as terminal
import prepare_local_reconstruction_20261026 as preparation

ROOT, OUT = preparation.ROOT, preparation.OUT


def reject(fn, raw):
    try:
        fn(raw)
    except (ValueError, TypeError):
        return True
    raise AssertionError('unexpected acceptance: '+raw[:80])


def no_labels(value):
    if isinstance(value, dict):
        assert not set(value) & {'local_criteria','final_criteria','correct_option_id','reference_match',
                                 'official_correct_text','case_rubric','analyst_design_target'}
        for v in value.values():
            no_labels(v)
    elif isinstance(value, list):
        for v in value:
            no_labels(v)


def main():
    manifest = io.read(OUT/'SOURCE_MANIFEST.json')
    for name, digest in manifest['sources'].items():
        assert preparation.sha(ROOT/name) == digest, name
    for name, digest in manifest['case_sha256'].items():
        assert preparation.sha(OUT/name) == digest, name
    tok = Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    count = lambda req: len(tok.encode(req['instructions']+json.dumps(req['schema']), add_special_tokens=False).ids)+256
    audit, lengths, source_quality = [], [], []
    index = io.read(OUT/'CASE_INDEX.json')
    schedule = io.read(OUT/'DESIGN_CONFIG.json')['schedule']
    cases = {}
    for entry in index:
        identifier = entry['case_id']
        case = cases[identifier] = io.read(OUT/'cases'/f'{identifier}.json')
        rows = preparation.rows(entry['source_run'])
        original = preparation.historical_packet(rows[entry['target_slot']])
        checker_original = preparation.historical_packet(rows[entry['checker_slot']])
        assert case['target_answer'] == io.strict_json(preparation.response_text(rows[entry['target_slot']]))
        expected = {k: copy.deepcopy(v) for k,v in original.items() if k != 'field_meanings'}
        expected.update(historical_work=case['target_answer'], historical_author=original['member'])
        assert case['receiver_context'] == expected
        assert case['checker_context'] == {k:checker_original[k] for k in ('task','member','public_sources','own_sources')}
        visible, isolated = [probe.local_request(case,m) for m in probe.METHODS]
        assert visible['instructions'].split('\nPACKET=')[0] == isolated['instructions'].split('\nPACKET=')[0]
        vp, ip = probe.packet(visible), probe.packet(isolated)
        assert vp.pop('historical_work') == case['target_answer']
        assert vp.pop('historical_author') == original['member']
        assert vp == ip
        assert set(ip) == {'task','member','public_sources','own_sources','local_question'}
        assert 'historical_work' not in ip
        carrier_raw = (ROOT/entry['carrier_raw']).read_text(encoding='utf-8')
        carrier = probe.decode_local(carrier_raw)
        carrier_core = dict(text=carrier['text'])
        finals = [probe.final_request(case, item) for item in (carrier, carrier_core)]
        assert finals[0] == finals[1], 'extra metadata forwarded'
        fp = probe.packet(finals[0])
        assert fp['local_reconstruction'] == dict(author=entry['checker'], text=carrier['text'])
        for key, value in case['receiver_context'].items():
            assert fp[key] == value
        for req in [visible, isolated, finals[0]]:
            no_labels(probe.packet(req))
            Draft202012Validator.check_schema(req['schema'])
        # This is a clearly labelled synthetic length extension of a full real carrier.
        stress_text = carrier['text']
        while len(tok.encode(stress_text).ids) < probe.CAP:
            stress_text += ' Synthetic length stress extension; no new task evidence.'
        stress_req = probe.final_request(case, dict(text=stress_text))
        lengths.append(dict(case_id=identifier, local_visible=count(visible), local_isolated=count(isolated),
                            final_real_carrier=count(finals[0]), final_synthetic_stress=count(stress_req)))
        # Legacy reason/artifact output stays a draft, not a new-protocol response.
        reject(lambda raw: terminal.decode(raw, case['receiver_context']), json.dumps(case['target_answer']))
        audit.append(dict(case_id=identifier, actual_target_and_checker_inputs_verified=True,
                          first_pair_only_draft_visibility_differs=True, source_access_matches_original=True,
                          real_extract_carrier_replayed=True, new_method_semantics_not_tested=True))
        source_quality.append(dict(case_id=identifier,
            unicode_replacement_characters_in_task_sources=sum(json.dumps(case['checker_context'][key],ensure_ascii=False).count('\ufffd')
                for key in ('task','public_sources','own_sources')),
            policy='Historical source encoding artifacts retained verbatim; no silent repair or new interpretation.'))
    assert len(audit) == 10 and len(schedule) == 32
    assert len({r['case_id'] for r in schedule}) == 8
    assert all(next(e for e in index if e['case_id']==r['case_id'])['scheduled'] for r in schedule)
    for pos in range(0,len(schedule),2):
        first, final = schedule[pos:pos+2]
        assert first['stage']=='local' and final['stage']=='final'
        assert final['depends_on']==first['unit']+'-local'
    # Replays are unmodified real modern final responses under their original tasks.
    modern = ROOT/'runs/evidence-first-live-20261025-r1'
    modern_rows = {r['attempt']:r for r in map(io.strict_json,(modern/'responses.jsonl').read_text(encoding='utf-8').splitlines())}
    modern_replay = []
    for slot in [18,36,63]:
        raw_path = modern/f'{slot:03d}.raw.txt'
        context = preparation.historical_packet(modern_rows[slot])
        decoded = terminal.decode(raw_path.read_text(encoding='utf-8'), context)
        modern_replay.append(dict(file=raw_path.relative_to(ROOT).as_posix(), sha256=preparation.sha(raw_path),
                                  choice=decoded['choice'], annotation_issues=decoded['annotation_issues']))
    first_bad = ['{}','[]','{"text":null}','{"text":0}','{"text":" "}',
                 '{"text":"x","text":"y"}','{"text":','{"text":"x"} extra','{"text":NaN}']
    for raw in first_bad:
        reject(probe.decode_local, raw)
    sample = next(iter(cases.values()))['receiver_context']
    final_bad = ['{}','{"choice":null}','{"choice":"bad","reasoning":"x"}',
                 '{"choice":null,"reasoning":" "}','{"choice":null,"reasoning":3}',
                 '{"choice":null,"choice":null,"reasoning":"x"}','{"choice":null,"reasoning":"x"']
    for raw in final_bad:
        reject(lambda text:terminal.decode(text,sample),raw)
    assert probe.decode_local('{"text":"Evidence is insufficient."}')['text']
    assert terminal.decode('{"choice":null,"reasoning":"No defensible answer can be offered."}',sample)['choice'] is None
    choice=sample['task']['choices'][0]['id']
    assert terminal.decode(json.dumps(dict(choice=choice,reasoning='Best supported option; some details remain unknown.')),sample)['choice']==choice
    maxima=max(
        r[k] for r in lengths for k in ('local_visible','local_isolated','final_real_carrier','final_synthetic_stress'))
    assert maxima < 16384
    by_id={r['case_id']:r for r in lengths}
    total=sum(by_id[r['case_id']]['local_'+('visible' if r['method']=='visible_draft' else 'isolated')]
              if r['stage']=='local' else by_id[r['case_id']]['final_synthetic_stress'] for r in schedule)
    io.write(OUT/'LOCAL_CHECKS.json',dict(scope='offline lineage/visibility/interface/length checks only',
        new_api_calls=0,cases=audit,unique_local_carrier_responses=len({e['carrier_raw'] for e in index}),
        unmodified_modern_final_replays=modern_replay,
        malformed_local_rejections=len(first_bad),malformed_final_rejections=len(final_bad),
        legacy_draft_rejections=10,valid_unknown_and_optional_metadata_supported=True,
        length_estimates=lengths,max_input_estimate=maxima,scheduled_stress_input_estimate=total,
        source_hashes_verified=True,schedule_requests=32,source_quality=source_quality,
        checker_sha256=preparation.sha(Path(__file__)),
        not_established=['No local or final output generated by the new method.',
                         'No live dependency runner, transport, runtime budget gate or launch freeze prepared.',
                         'No semantic success or autonomous target-selection result.',
                         'Synthetic stress is not a bound for every possible future response.']))
    print(json.dumps(dict(cases=10,real_local_replay_uses=10,
                         unique_local_carrier_responses=len({e['carrier_raw'] for e in index}),real_modern_final_replays=3,
                         invalid_core_rejections=len(first_bad)+len(final_bad),legacy_draft_rejections=10,
                         max_input_estimate=maxima,scheduled_stress_input_estimate=total,new_api_calls=0)))


if __name__=='__main__':
    main()

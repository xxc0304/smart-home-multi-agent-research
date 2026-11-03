"""Replay old contracts as old contracts; never label legacy prose as new operations."""
from pathlib import Path
import json
from coreta.handoff.contracts import HandoffContracts
from coreta.schemas import ProtocolError
from coreta.local_work.engine import WorkSession


def replay(root, count=12):
    root = Path(root)
    rows = []
    for index in range(1, count + 1):
        raw_path = root / f'{index:02d}.raw.txt'
        req_path = root / 'actual_requests' / f'{index:02d}.json'
        raw = raw_path.read_text(encoding='utf-8')
        req = json.loads(req_path.read_text(encoding='utf-8'))
        packet = json.loads(req['instructions'].split('PACKET=', 1)[1])
        old = HandoffContracts.decode(raw, req['schema'])
        originals = packet['public_sources'] + packet['own_sources']
        visible = {s['ref']: s['content'] for s in originals}
        refs = old.get('source_ids', [])
        absent = [ref for ref in refs if ref not in visible]
        # Rebuild only the source/access carrier for the common packet interface.
        actor = packet['member']
        task = dict(task_id=packet['task']['task_id'], question=visible['TASK'], members=[actor],
                    sources=[dict(id=s['ref'], content=s['content'], owner='public', kind='original')
                             for s in packet['public_sources'] if s['ref'] != 'TASK'] +
                            [dict(id=s['ref'], content=s['content'], owner=actor, kind='original')
                             for s in packet['own_sources']])
        session = WorkSession(task)
        carrier = session.packet(actor, 0)
        copied = {s['id']: s['content'] for s in carrier['sources']}
        if copied != visible:
            raise AssertionError('source content or access changed in common carrier replay')
        incompatible = session.apply(actor, raw, carrier)
        rows.append(dict(raw_file=str(raw_path), original_request=str(req_path),
                         old_schema='valid', source_refs=refs, invisible_refs=absent,
                         source_expansion=[dict(id=ref, content=visible[ref]) for ref in refs if ref in visible],
                         raw_characters=len(raw),
                         new_schema_expected_status='unreadable_core',
                         new_schema_actual_status=incompatible['status'],
                         semantics='No operation extracted; legacy output is not new-schema generation coverage'))
    return dict(replay_type='historical_complete_old_contract_and_common_source_interface',
                count=len(rows), old_contract_valid=sum(r['old_schema'] == 'valid' for r in rows),
                all_refs_visible=all(not r['invisible_refs'] for r in rows),
                all_new_schema_incompatible_as_expected=all(r['new_schema_actual_status'] == 'unreadable_core' for r in rows),
                new_work_generation_coverage=0, rows=rows)

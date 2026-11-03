"""Prepare exactly the ten unattempted slots as a separate source-handle batch."""
from pathlib import Path
import local_judgment_frontend as interface
import prepare_local_judgment_calibration as original
import local_judgment_handle_contract as contract

ROOT = original.ROOT
PARENT_PREPARED = ROOT / 'runs/local-judgment-moon-calibration-prepared-20261025-r2'
PARENT_LIVE = ROOT / 'runs/local-judgment-moon-calibration-live-20261025-r1'
make_request = contract.make_request


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError('new directory required')
    plan = interface.read(PARENT_PREPARED / 'CALIBRATION_PLAN.json')
    progress = interface.read(PARENT_LIVE / 'progress.json')
    review = interface.read(PARENT_LIVE / 'review.json')
    if progress['status'] != 'stopped' or progress['attempts'] != 14:
        raise ValueError('parent no longer matches stopped batch')
    unattempted = [r for r in review['rows'] if r['status'] == 'not_run']
    if [r['slot'] for r in unattempted] != list(range(15, 25)):
        raise ValueError('expected only original slots15..24')
    output.mkdir(parents=True)
    roster = []
    for old in unattempted:
        scheduled = plan['schedule'][old['slot']-1]
        if any(old[k] != scheduled[k] for k in ['item','condition','repeat','request','member']):
            raise ValueError('parent progress/schedule differs')
        packet_name = old['item'] + '-' + old['condition'] + '.json'
        packet = interface.read(PARENT_PREPARED / 'packets' / packet_name)
        old_request = interface.read(PARENT_PREPARED / scheduled['request'])
        actual_packet = interface.strict_json(old_request['instructions'].split('PACKET=',1)[1])
        if packet != actual_packet:
            raise ValueError('parent request packet differs')
        interface.write(output / 'packets' / packet_name, packet)
        interface.write(output / scheduled['request'], make_request(packet))
        roster.append(dict(scheduled, original_slot=old['slot']))
    interface.write(output / 'CALIBRATION_PLAN.json', dict(
        status='NEW_SUPPLEMENT_NOT_PARENT_RESUME', contract_version='source-handles/2',
        schedule=roster, max_requests=10, per_request_output_cap=1536, max_total_output_tokens=15360,
        parent_attempts=14, parent_admitted=13, parent_failed_slot_not_repeated=14,
        original_slots=list(range(15,25)), new_slots=list(range(1,11)),
        unique_parent_scenarios=1, local_questions=3,
        analysis='Report supplement separately; only item05/06 have two same-contract pairs; item04 only repeat2 is paired in this supplement.',
        no_retry=True, no_automatic_expansion=True,
        stop_policy='Single unreadable independent slot quarantined; two consecutive stop. Transport/unknown usage/budget/frozen mismatch stop immediately.',
        provenance=[dict(path=str(path),sha256=interface.digest(path)) for path in [
            PARENT_PREPARED/'manifest.json',PARENT_LIVE/'progress.json',PARENT_LIVE/'review.json']] ))
    return dict(request_templates=len(list((output/'requests').glob('*.json'))),
                max_attempts=10,original_slots=list(range(15,25)),network_calls=0)

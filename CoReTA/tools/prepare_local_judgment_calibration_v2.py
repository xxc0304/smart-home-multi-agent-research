"""New-contract candidate only; never resumes or edits the stopped v1 batch."""
from pathlib import Path
import local_judgment_frontend as interface
import prepare_local_judgment_calibration as original
import local_judgment_handle_contract as contract

ROOT = original.ROOT
PACK, ITEMS = original.PACK, original.ITEMS
build_packet = original.build_packet
make_request = contract.make_request


def prepare(output):
    output = Path(output)
    result = original.prepare(output)
    plan = interface.read(output / 'CALIBRATION_PLAN.json')
    plan.update(contract_version='source-handles/2',
                independent_item_error_policy='quarantine unreadable item, no retry, continue next independent slot; stop after 2 consecutive unreadable outputs',
                global_stop_policy='transport failure, unknown usage, budget violation, frozen input mismatch')
    interface.write(output / 'CALIBRATION_PLAN.json', plan)
    for path in (output / 'packets').glob('*.json'):
        packet = interface.read(path)
        interface.write(output / 'requests' / path.name, make_request(packet))
    return result

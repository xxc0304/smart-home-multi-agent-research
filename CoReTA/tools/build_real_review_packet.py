"""Offline real packet construction; no model observations or transport."""
import hashlib
import json
from pathlib import Path
from tokenizers import Tokenizer
from coreta.review_packet import build_packet
from coreta.minimal_review import ReviewAdapter,RepairBudget
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/minimal-real-packet-20261020'
def main():
    if OUT.exists():raise ValueError('Refuse overwrite')
    source=ROOT/'runs/math140-correct-repair-review-v3-20261020/public_component_input.json'
    data=json.loads(source.read_text(encoding='utf-8'));packet,mapping=build_packet(data)
    OUT.mkdir();tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    adapter=ReviewAdapter(OUT/'adapter',ROOT/'design/convergence/minimal_review.schema.json',token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids),shared_budget=RepairBudget(2,0))
    request=adapter.request(packet)
    for name,value in [('packet',packet),('mapping',mapping),('prepared_request',request)]:
        (OUT/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    log=json.loads((OUT/'adapter/requests.jsonl').read_text(encoding='utf-8').splitlines()[-1])
    summary={'scope':'Offline mapping of real public state only; no review response, no task success',
        'candidate_hash_unchanged':mapping['candidate_hash']==packet['candidate_identity']['hash'],
        'issues':len(packet['issues']),'original_cases':len(mapping['case_handles']),
        'historical_object_count':len(packet['historical_objects']),'input_estimate':log['input_estimate'],
        'input_limit':32768,'external_api_requests':0,'repair_budget_scope':'independent component; full workflow must inject shared task budget',
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source':str(source)}
    (ROOT/'engineering/REAL_REVIEW_PACKET_20261020.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary))
if __name__=='__main__':main()

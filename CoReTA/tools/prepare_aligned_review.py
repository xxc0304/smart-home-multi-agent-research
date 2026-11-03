"""Offline contract-alignment check; no external model request."""
import hashlib
import json
from pathlib import Path
from tokenizers import Tokenizer
from coreta.aligned_review import ReviewAdapter,align_packet
from coreta.protocol_stability import StabilityClient
from coreta.minimal_review_transport import provider_payload
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/aligned-review-offline-20261020'
def main():
    if OUT.exists():raise ValueError('Refuse overwrite')
    source=ROOT/'runs/minimal-real-packet-20261020/packet.json';packet=json.loads(source.read_text(encoding='utf-8'))
    tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'));counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    adapter=ReviewAdapter(OUT,ROOT/'design/convergence/aligned_review.schema.json',token_counter=counter)
    request=adapter.request(packet);cfg=json.loads((ROOT/'config/deepseek_flash_inspection.json').read_text())
    client=StabilityClient(cfg,adapter.log,token_counter=counter);size=client.size(provider_payload(client,request,8192))
    raw=json.loads((ROOT/'runs/minimal-review-component-20261020/live/responses.jsonl').read_text(encoding='utf-8').splitlines()[-1])['raw']
    replay=adapter.consume(request['request_id'],raw,packet['candidate_identity'])
    (OUT/'packet.json').write_text(json.dumps(align_packet(packet),ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
    result={'scope':'Offline alignment and unchanged-output failure replay only; no new model response',
        'candidate_unchanged':packet['candidate_identity']==request['packet']['candidate_identity'] and packet['current_targets']==request['packet']['current_targets'],
        'provider_input_estimate':size,'input_limit':32768,'external_api_requests':0,
        'old_raw_output_sha256':hashlib.sha256(raw.encode()).hexdigest(),'old_response_rewritten':False,
        'replayed_issue_statuses':{k:v['status'] for k,v in replay['issues'].items()},
        'coverage_modes':{k:v['task_coverage_mode'] for k,v in request['packet']['issues'].items()},
        'semantic_math_error_corrected_by_program':False}
    (ROOT/'engineering/REVIEW_SEMANTIC_ALIGNMENT_VALIDATION_20261020.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':main()

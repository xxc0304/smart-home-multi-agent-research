"""Trace actual answer spans to already-visible evidence; manual diagnostic selection."""
import copy
from pathlib import Path
from jsonschema import Draft202012Validator
from tokenizers import Tokenizer
import local_judgment_frontend as io
import local_reconstruction_probe as old
import minimal_final_answer_contract as terminal
import receiver_question_context_v2 as handoff
import inference_link_probe_v1 as probe

ROOT=io.ROOT
PARENT=ROOT/'runs/example-adaptation-live-20261026-r1'
OUT=ROOT/'research/inference-link-walkthrough-20261027-v1'
SPECS=[
    dict(id='004-identity',slot=38,target='Mr. X is the only suspect publicly described as having consumed alcohol while driving a car',
         originals=['PUBLIC.1','S01'],peers=[('A2','S02','less than 30')],
         assessment='The public text states prior drinking and travelling together, not an explicit named-driver or measured-alcohol identification. Do not promote qualitative matching to direct original identification. Rejecting this link does not independently identify the culprit.',
         use='Check which part of the alleged own-source conflict is actually an inference; preserve the separately reported age condition.'),
    dict(id='023-notice',slot=19,target="Grand Oak's notice requirement is a categorical scheduling conflict",
         originals=['PUBLIC.2'],peers=[('A2','S02','last-minute bookings')],
         assessment='Usually is not an unconditional prohibition. The shared phone-booking report supplies a current possible route, not a confirmed booking or proof of catering/capacity.',
         use='Test whether the purported hard exclusion follows from the given rule and whether the exception changes its applicability.'),
    dict(id='011-time-supported',slot=49,target='at least two working restrooms (ventilation and water) expected within an hour, leaving roughly an hour of margin inside the two-hour window',
         originals=['TASK'],peers=[('A2','S02','at least two working restrooms')],
         assessment='The stated expected one-hour restoration fits the two-hour window. Preserve this conditional comparison; it does not prove completed repairs or full-day safety.',
         use='A positive preservation guard; selected for checking does not mean it must be changed.'),
]


def inputs(slot):
    path=PARENT/'actual_requests'/f'{slot:03d}.json'
    req=io.read(path);packet=probe.packet(req)
    raw_path=PARENT/f'{slot:03d}.raw.txt';answer=io.read(raw_path)
    return path,packet,raw_path,answer


def anchors(packet,spec):
    result=[]
    for ref in spec['originals']:
        matches=[('public_sources',i,x) for i,x in enumerate(packet['public_sources']) if x['ref']==ref]
        matches += [('own_sources',i,x) for i,x in enumerate(packet['own_sources']) if x['ref']==ref]
        if len(matches)!=1:raise ValueError('ambiguous original reference')
        field,i,x=matches[0]
        result.append(dict(kind='directly_visible_original',ref=ref,text=x['content'],pointer=[field,i,'content']))
    for author,ref,needle in spec['peers']:
        found={}
        for field in ('facts','conditions'):
            for i,row in enumerate(packet['shared_contributions'][author].get(field,[])):
                if row.get('source')==ref and needle in row.get('quote',''):
                    found.setdefault(row['quote'],['shared_contributions',author,field,i,'quote'])
        if not found:raise ValueError('shared span not in actual receiver packet')
        for text,pointer in found.items():
            result.append(dict(kind='already_shared_quoted_span',author=author,ref=ref,text=text,pointer=pointer))
    return result


def at(value,pointer):
    for key in pointer:value=value[key]
    return value


def main():
    if OUT.exists():raise ValueError('new walkthrough version required')
    tokenizer=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    evidence=[];reviews=[];replays=[];sizes=[]
    for spec in SPECS:
        path,packet,raw_path,answer=inputs(spec['slot'])
        original=copy.deepcopy(packet)
        packet.pop('worked_examples',None) # No simultaneous few-shot intervention.
        packet['historical_work']=copy.deepcopy(answer)
        packet['historical_author']=packet['member']
        packet=handoff.contextualize(packet,question_author=packet['local_reconstruction']['author'])
        assert answer['reasoning'].count(spec['target'])==1
        start=answer['reasoning'].index(spec['target'])
        selected=dict(text=spec['target'],field='historical_work.reasoning',start=start,end=start+len(spec['target']))
        source_anchors=anchors(original,spec)
        for anchor in source_anchors:assert at(original,anchor['pointer'])==anchor['text']
        case=dict(case_id=spec['id'],receiver_context=packet,selected_statement=selected,visible_anchors=source_anchors)
        io.write(OUT/'cases'/f"{spec['id']}.json",case)
        requests=[probe.first_request(case,m) for m in probe.METHODS]
        assert probe.packet(requests[0])==probe.packet(requests[1])
        for method,req in zip(probe.METHODS,requests):
            Draft202012Validator.check_schema(req['schema'])
            io.write(OUT/'request_examples'/f"{spec['id']}-{method}.json",req)
            sizes.append(len(tokenizer.encode(req['instructions']).ids)+len(tokenizer.encode(str(req['schema'])).ids)+256)
        # Complete real text carrier from the earlier same-task provider stage.
        earlier=io.read(ROOT/'research/isolated-reconstruction-20261026-v1/CASE_INDEX.json')
        old_id=original['task']['task_id'].split('-')[-1]
        entry=next(x for x in earlier if x['task']==old_id)
        carrier_path=ROOT/entry['carrier_raw'];carrier=old.decode_local(carrier_path.read_text(encoding='utf-8'))
        final=probe.final_request(case,carrier)
        assert final==probe.final_request(case,dict(text=carrier['text']))
        fpacket=probe.packet(final)
        assert fpacket['inference_link_review']['text']==carrier['text']
        assert {k:v for k,v in fpacket.items() if k not in {'selected_statement','inference_link_review'}}==packet
        io.write(OUT/'request_examples'/f"{spec['id']}-final-HISTORICAL-CARRIER.json",final)
        assert 'local_question' not in packet and packet['prior_local_question']['addressed_member']==packet['local_reconstruction']['author']
        # Target markers are source offsets only; analyst verdicts stay offline.
        assert 'assessment' not in str(probe.packet(requests[0]).keys())
        reviews.append(dict(case_id=spec['id'],assessment=spec['assessment'],use=spec['use'],
            status='manual design interpretation, not a hidden correct repair or autonomous target selection'))
        evidence.append(dict(case_id=spec['id'],slot=spec['slot'],request_path=path.relative_to(ROOT).as_posix(),
            request_sha256=io.digest(path),answer_path=raw_path.relative_to(ROOT).as_posix(),answer_sha256=io.digest(raw_path),
            exact_target_offset=[start,start+len(spec['target'])],visible_anchors_verified=len(source_anchors),
            transformations=['remove demonstrations','target actual latest answer rather than older archived draft',
                             'explicit original local-question addressee','repeat only already-visible source spans as selected anchors']))
        replays.append(dict(case_id=spec['id'],carrier_path=carrier_path.relative_to(ROOT).as_posix(),
            carrier_sha256=io.digest(carrier_path),kind='real EXTRACT text carrier, not a real inference-link review'))
    boundaries=[]
    for identifier,slot,note in [
        ('009-risk-boundary',45,'Large ICU and no free beds can coexist. Whether a temporary shortage or unknown bypass justifies this immediate transfer is a decision-warrant question; do not fabricate a hard semantic error or a unique fully proved alternative.'),
        ('023-access-boundary',56,'Only access ROAD does not formally exclude every imaginable non-road access. An imagined water route is not evidence of a feasible route for this event. Keep logical possibility separate from supported practical choice.')]:
        path,packet,raw_path,answer=inputs(slot)
        io.write(OUT/'boundary_archive'/f'{identifier}.json',dict(actual_packet=packet,actual_answer=answer))
        boundaries.append(dict(case_id=identifier,slot=slot,note=note,scheduled=False,
            request_sha256=io.digest(path),answer_sha256=io.digest(raw_path)))
    io.write(OUT/'EVIDENCE_INDEX.json',evidence)
    io.write(OUT/'offline_only/WALKTHROUGH_NOTES.json',reviews)
    io.write(OUT/'offline_only/BOUNDARIES.json',boundaries)
    io.write(OUT/'LOCAL_CHECKS.json',dict(new_api_calls=0,cases=3,exact_target_spans=3,matched_first_packets=3,
        source_anchors_checked=sum(x['visible_anchors_verified'] for x in evidence),real_carrier_replays=replays,
        explicit_question_addressee=True,max_first_input_estimate=max(sizes),
        boundaries_not_scheduled=2,not_established=['No generated model review or repair.','No autonomous target/evidence selection.',
        'No live runner, launch manifest, transport failure gate, budget freeze or authorization.']))
    io.write(OUT/'SOURCE_MANIFEST.json',dict(code_sha256={p.relative_to(ROOT).as_posix():io.digest(p) for p in [Path(__file__),Path(probe.__file__),Path(handoff.__file__)]},
        files={p.relative_to(OUT).as_posix():io.digest(p) for p in OUT.rglob('*.json')}))
    print(dict(cases=3,boundaries=2,source_anchors=sum(x['visible_anchors_verified'] for x in evidence),new_api_calls=0))


if __name__=='__main__':main()

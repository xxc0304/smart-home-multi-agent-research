"""Offline lossless evidence/analysis separation; no API or gold access."""
import copy
from pathlib import Path
import local_judgment_frontend as io

ROOT=io.ROOT
SOURCE=ROOT/'runs/confidence-visibility-live-20261026-r2'
OUT=ROOT/'research/decision-test-design-20261026/evidence-layer-prototype-r2'

def separate(packet):
    p=copy.deepcopy(packet);documents={};occurrences=[];bindings=[]
    def bind(items,location):
        refs=[]
        for item in items:
            ref=item['ref']
            if ref in documents and documents[ref]!=item:raise ValueError('conflicting source text: '+ref)
            documents[ref]=copy.deepcopy(item);refs.append(ref)
            occurrences.append(copy.deepcopy(item))
        bindings.append(dict(location=location,refs=refs))
        return refs
    p['public_source_refs']=bind(p.pop('public_sources'),'public_sources')
    p['originally_owned_source_refs']=bind(p.pop('own_sources'),'own_sources')
    for i,r in enumerate(p['contributor_reports']):
        r['disclosed_source_refs']=bind(r.pop('disclosed_originals'),f'contributor_reports/{i}/disclosed_originals')
    # Preserve repeated source occurrences. Deduplication would confound the
    # representation comparison with repetition frequency.
    p['available_original_documents']=occurrences
    return p,bindings

def restore(packet):
    p=copy.deepcopy(packet);docs={x['ref']:x for x in p.pop('available_original_documents')}
    p['public_sources']=[copy.deepcopy(docs[r]) for r in p.pop('public_source_refs')]
    p['own_sources']=[copy.deepcopy(docs[r]) for r in p.pop('originally_owned_source_refs')]
    for report in p['contributor_reports']:
        report['disclosed_originals']=[copy.deepcopy(docs[r]) for r in report.pop('disclosed_source_refs')]
    return p

def main():
    if OUT.exists():raise ValueError('do not overwrite existing audit')
    cases=[]
    for row in io.read(SOURCE/'review.json')['rows']:
        if row['stage']!='final' or row['method']!='hidden':continue
        req=io.read(SOURCE/'actual_requests'/f"{row['slot']:03d}.json")
        original=io.strict_json(req['instructions'].split('PACKET=',1)[1])
        layered,bindings=separate(original)
        assert restore(layered)==original
        assert 'available_original_documents' not in original
        case=f"{row['task']}-{row['receiver']}"
        io.write(OUT/case/'original.json',original)
        io.write(OUT/case/'layered.json',layered)
        io.write(OUT/case/'bindings.json',bindings)
        cases.append(dict(case=case,source_slot=row['slot'],source_sha256=io.digest(SOURCE/'actual_requests'/f"{row['slot']:03d}.json"),
                          unique_originals=len({x['ref'] for x in layered['available_original_documents']}),
                          source_occurrences=len(layered['available_original_documents']),
                          original_source_occurrences=len(original['public_sources'])+len(original['own_sources'])+sum(len(x['disclosed_originals']) for x in original['contributor_reports']),
                          lossless_roundtrip=True))
        assert cases[-1]['source_occurrences']==cases[-1]['original_source_occurrences']
    io.write(OUT/'AUDIT.json',dict(network_calls=0,model_calls=0,case_count=len(cases),cases=cases,
        scope='Representation prototype only; no semantic or effectiveness claims; no gold read; initial private ownership retained separately from present availability'))
    print('Six real contexts transformed and restored exactly; zero model/API calls.')

if __name__=='__main__':main()

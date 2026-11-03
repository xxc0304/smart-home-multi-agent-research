"""Offline indexing of actual reasoning; marker counts are not causal labels."""
import re
import local_judgment_frontend as io

ROOT=io.ROOT
OUT=ROOT/'research/imp-mechanism-audit-20261026'

def main():
    run=ROOT/'runs/imp-confirmation-live-20261026-r1'
    rows=[r for r in io.read(run/'review.json')['rows'] if r['task']=='008']
    marker=re.compile(r'\blie[ds]?\b|\bfalse\b|fabricat|decep',re.I)
    indexed=[]
    for row in rows:
        text=row['answer']['reasoning'];flags=[m.group() for m in marker.finditer(text)]
        indexed.append(dict(slot=row['slot'],method=row['method'],round=row['round'],receiver=row['receiver'],repeat=row['repeat'],
            choice=row['answer']['choice'],marker=bool(flags),marker_words=flags,reasoning=text,
            raw_sha256=io.digest(run/f"{row['slot']:03d}.raw.txt")))
    assert len(indexed)==32
    totals={}
    for choice in ('option_1','option_2','option_3'):
        selected=[r for r in indexed if r['choice']==choice]
        totals[choice]=dict(outputs=len(selected),markers=sum(r['marker'] for r in selected),slots=[r['slot'] for r in selected])
    bundle=io.read(ROOT/'runs/imp-confirmation-prepared-20261026-r1/tasks/008.json')
    io.write(OUT/'008_OUTPUT_INDEX.json',dict(rows=indexed,totals=totals,
        method='Lexical markers for indexing, then all 32 explanations read manually; markers are not an automated factual correctness evaluator',
        independent_blind=False,source_documents=bundle['documents'],source_task=bundle['task'],
        caveats=['Repeated/related outputs are not independent observations','Co-occurrence does not identify a causal error source','Reference correctness does not certify reasoning correctness','Do not remove a task to improve results']))
    old=ROOT/'runs/imp-adaptation-live-20261026-r1';new=run
    cases=[]
    for label,folder,slots in [('restatement_loss',old,[19,21,24]),('opinion_influence_030',old,[7,9,10,13]),('opinion_influence_007',new,[39,42,43,50,51,54,55])]:
        review=io.read(folder/'review.json')['rows']
        cases.append(dict(label=label,run=folder.relative_to(ROOT).as_posix(),outputs=[review[s-1] for s in slots]))
    io.write(OUT/'SUCCESS_PROCESS_CASES.json',dict(cases=cases,causal_limit='Examples support mechanism hypotheses; no factorial isolation of raw-evidence restoration, duplication and opinion filtering'))
    io.write(OUT/'RESTORATION_INPUT_PAIR.json',dict(
        sender_initial=io.read(old/'review.json')['rows'][18],
        standard_receiver_request=io.read(old/'actual_requests/021.json'),
        imp_receiver_request=io.read(old/'actual_requests/024.json'),
        scope='Same 033 repeat-1 receiver A2 and own initial state; different inbox packages; original record restores outage recovery omitted in sender message'))
    print(totals)

if __name__=='__main__':main()

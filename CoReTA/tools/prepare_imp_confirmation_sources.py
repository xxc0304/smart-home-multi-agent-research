"""Deterministic native input adapter; no model calls and no task-outcome selection."""
import re
import local_judgment_frontend as io

ROOT=io.ROOT
OUT=ROOT/'research/imp-confirmation-20261026/source_packets-r2'

def cells(text,choices):
    current=None;result=[];mapping=[]
    for line in text.splitlines():
        line=line.strip()
        if not line:continue
        if line.endswith(':') and line[:-1] in choices:current=choices.index(line[:-1])+1;continue
        match=re.fullmatch(r'-\s*\(([a-j])\)\s*([YN])',line)
        if current is None or match is None:raise ValueError('unrecognized source table line: '+line)
        criterion,value=match.groups();ref=f'RFP.C{current}.{criterion}'
        result.append(dict(ref=ref,content=f'{choices[current-1]}: ({criterion}) {value}'))
        mapping.append(dict(ref=ref,company=choices[current-1],original_line=line))
    if not result:raise ValueError('empty source table')
    return result,mapping

def main():
    if OUT.exists():raise ValueError('new source directory required')
    source=ROOT/'data/task-source-audit-20261021/hiddenbench.json'
    split=io.read(ROOT/'data/dataset-selection-20261022/SELECTION_MANIFEST.json')
    assert io.digest(source)==split['source_sha256']
    records={r['id']:r for r in io.read(source)};selection=io.read(ROOT/'research/imp-confirmation-20261026/SELECTION.json')
    assert selection['ids']==[7,8] and not selection['evaluation_pool_consumed']
    mappings=[]
    for n in selection['ids']:
        raw=records[n];t=f'{n:03d}';choices=raw['possible_answers']
        task=dict(task_id='hb-imp-confirm-'+t,scenario=raw['description'],shared_information=raw['shared_information'],
            choices=[dict(id=f'option_{i+1}',text=x) for i,x in enumerate(choices)],instruction='Follow the decision requirement in the task and explain genuine unresolved conditions.')
        public=[dict(ref='TASK',content=raw['description'])]
        for j,text in enumerate(raw['shared_information'],1):
            if n==7:
                units,links=cells(text,choices);public.extend(units);mappings.extend(dict(task=t,origin=f'PUBLIC.{j}',**x) for x in links)
            else:public.append(dict(ref=f'PUBLIC.{j}',content=text))
        for j,text in enumerate(raw['hidden_information'],1):
            member=f'A{j}'
            if n==7:
                own,links=cells(text,choices);mappings.extend(dict(task=t,origin='PRIVATE.'+member,**x) for x in links)
            else:own=[dict(ref='PRIVATE.'+member,content=text)]
            io.write(OUT/'members'/t/f'{member}.json',dict(task=task,member=member,public_sources=public,own_sources=own))
        io.write(OUT/'offline'/f'{t}.json',dict(correct_option_id=next(c['id'] for c in task['choices'] if c['text']==raw['correct_answer']),metric='reference_choice_match'))
    # A source cell has one underlying company/criterion identity, even when repeated in checklists.
    values={}
    for packet in (OUT/'members/007').glob('*.json'):
        row=io.read(packet)
        for unit in row['public_sources'][1:]+row['own_sources']:
            if unit['ref'] in values:assert values[unit['ref']]==unit['content']
            values[unit['ref']]=unit['content']
    assert len(values)==30  # Three companies x ten original criteria, no added rows.
    io.write(OUT/'TABLE_MAPPING.json',mappings)
    io.write(OUT/'SOURCE_MANIFEST.json',dict(source_sha256=io.digest(source),selection_sha256=io.digest(ROOT/'research/imp-confirmation-20261026/SELECTION.json'),
        table_cells=30,network_calls=0,adapter='007 deterministic company-header plus criterion/value cells; 008 unchanged text source records',
        files={f.relative_to(OUT).as_posix():io.digest(f) for f in OUT.rglob('*.json')}))
    print('Selected 007/008 native packets prepared; 30 consistent RFP cells, no new facts.')

if __name__=='__main__':main()

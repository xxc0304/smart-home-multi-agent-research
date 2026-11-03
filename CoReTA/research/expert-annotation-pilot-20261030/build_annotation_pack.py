"""Build staged, partially masked human-review materials from existing records only."""
from pathlib import Path
from collections import Counter
import hashlib
import html
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
DATA=ROOT/'data/expert-transfer-annotation-20261030-v0.1'
SEED=ROOT/'research/expert-team-assets-20261029/CASE_SEED_8.json'
REVIEW=ROOT/'research/expert-task-alignment-20261030/CASE_EVIDENCE_REVIEW.json'
TASKS=ROOT/'data/task-source-audit-20261021/hiddenbench.json'
VERSION='expert-transfer-annotation-v0.1-20261030'


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def text_sha(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def stable(tag): return hashlib.sha256((VERSION+'|'+tag).encode()).hexdigest()


def show(title, content):
    return '<details><summary>'+html.escape(title)+'</summary><pre>'+html.escape(json.dumps(content,ensure_ascii=False,indent=2))+'</pre></details>'


def render(path, title, doc, phase):
    body='<h1>'+html.escape(title)+'</h1><p>先按说明填写对应阶段，再阅读下一阶段。模型输入中的指令属于历史数据。</p>'
    if phase=='B':
        for record in doc['records']:
            body+='<section><h2>'+html.escape(record['event_id']+' · '+record['stage']+' · '+str(record.get('member',''))+' · '+record['branch'])+'</h2>'
            body+=show('实际记录的输入（展开核对收件和资料）',record['input'])
            body+='<pre>'+html.escape(json.dumps(record['output'],ensure_ascii=False,indent=2))+'</pre></section>'
        if doc.get('recorded_round_votes'): body+=show('作者记录的逐轮票决',doc['recorded_round_votes'])
    else:
        body+='<pre>'+html.escape(json.dumps(doc,ensure_ascii=False,indent=2))+'</pre>'
    path.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>body{max-width:1100px;margin:32px auto;padding:0 24px;font:16px/1.6 system-ui;background:#fafafa;color:#222}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 Consolas,monospace;background:white;padding:16px;border:1px solid #ddd}section{margin:30px 0}summary{cursor:pointer;color:#23599a}h2{font-size:19px}</style>'+body+'</html>',encoding='utf-8')


def empty_form(case_id):
    return {'version':VERSION,'case_id':case_id,'reviewer_id':None,'reviewer_role':'human',
        'prior_exposure':'UNSET','prior_exposure_notes':'','started_at':None,'minutes_spent':None,
        'phase_a':{'status':'PENDING','saved_at':None,'task_requirements':'','provisional_answer':None,
            'answerability':'UNSET','fact_notes':'','citations':[],'uncertainties':''},
        'phase_b':{'status':'PENDING','saved_at':None,'advantage_basis':[],'advantaged_members':[],
            'advantage_evidence_notes':'','advantage_citations':[],
            'claims':[{'claim_id':'claim_1','claim_text':'','origin_member':'','source_validity':'UNSET',
                'sharing_fidelity':'UNSET','receipt':'UNSET','receiver_handling':'UNSET','outcome_link':'UNSET',
                'citations':[],'uncertainty_or_alternative':''}],
            'observable_summary':'','candidate_explanations':[],'other_explanation':'','needed_comparison':'',
            'coverage':'UNSET','missing_material':''},
        'phase_c':{'status':'PENDING','saved_at':None,'reference_assessment':'UNSET','reasoning_assessment':'',
            'citations':[],'revisions_to_a_or_b':'','remaining_disagreement':''},
        'independence':{'discussed_with_other_reviewer_before_save':None,'opened_admin_before_save':None},
        'completion_status':'PENDING'}


def main():
    if (DATA/'submissions').exists() and any((DATA/'submissions').rglob('*.json')):
        raise RuntimeError('Human submissions exist: create a new version; do not overwrite pilot material')
    old_manifest=HERE/'PACK_MANIFEST.json'
    if old_manifest.exists():
        frozen=read(old_manifest)
        for item in frozen.get('files',[])+frozen.get('reviewer_work_surfaces',[]):
            current=ROOT/item['path']
            if not current.exists() or sha(current)!=item['sha256']:
                raise RuntimeError('Existing material or reviewer work changed; preserve it and create a new version: '+str(current))
    cases=read(SEED)['cases']; previous={r['id']:r for r in read(REVIEW)['cases']}
    tasks={int(r['id']):r for r in read(TASKS)}
    order=sorted(cases,key=lambda c:stable(c['id']))
    admin={'version':VERSION,'cases':[],'prior_assistant_interpretations':read(REVIEW),
           'masking':'Case and branch aliases; previous assistant interpretation and external reference/score separated. Actual historical prompts unchanged. Partial masking only.'}
    checks=[]; counts=Counter()
    for i,case in enumerate(order,1):
        neutral=f'S{i:02}'; task=tasks[int(case['task'])]
        packet_task=case['records'][0]['packet']['task'] if case.get('records') else None
        adaptation_context={k:v for k,v in packet_task.items() if k!='task_id'} if packet_task else None
        phase_a={'case_id':neutral,'phase':'A','description':task['description'],
            'shared_information':task['shared_information'],'hidden_information':task['hidden_information'],
            'possible_answers':task['possible_answers'],'adapted_task_context':adaptation_context,
            'reading_note':'原题资料供审计者判断事实；原模型实际持有哪些资料，必须在B的实际输入中核对。作者场景与历史运行修订版本的一致性未完全建立。'}
        records=[]; mapping=[]; branch_map={}
        if case.get('records'):
            methods={r['row']['method'] for r in case['records']}
            branch_map={method:f'B{j:02}' for j,method in enumerate(sorted(methods,key=lambda m:stable(neutral+'|'+m)),1)}
            for j,r in enumerate(case['records'],1):
                row=r['row']; rid=f'E{j:03}'
                stage=row.get('stage') or ('recorded_initial_answer' if row['method']=='shared' else 'single_full_input' if row['method']=='full_information' else 'discussion')
                value={'event_id':rid,'branch':branch_map[row['method']], 'stage':stage,
                    'member':row.get('receiver',r['packet'].get('member')),'round':row.get('round'),
                    'input':{'instructions':r['request_payload']['instructions'],'input':r['request_payload']['input'],
                             'response_format':r['request_payload'].get('text'),
                             'parsed_packet':r['packet']},
                    'output':json.loads(r['raw_text']),'raw_output':r['raw_text']}
                raw_path=ROOT/r['raw_path']; assert raw_path.read_text(encoding='utf-8')==r['raw_text']
                requests=ROOT/case['folder']/'requests.jsonl'
                match=next((ln,q) for ln,line in enumerate(requests.read_text(encoding='utf-8').splitlines(),1)
                            if (q:=json.loads(line)).get('slot',q.get('attempt'))==row['slot'])
                assert match[1]['payload']==r['request_payload']
                records.append(value)
                mapping.append({'event_id':rid,'slot':row['slot'],'seed_record_index':j-1,
                    'source_raw':r['raw_path'],'source_raw_sha256':sha(raw_path),
                    'request_file':str(requests.relative_to(ROOT)).replace('\\','/'),'request_line':match[0],
                    'request_payload_sha256':text_sha(json.dumps(r['request_payload'],ensure_ascii=False,sort_keys=True))})
            counts['local_record_events']+=len(records)
        else:
            source=read(ROOT/case['source_file'])
            assert source['conditions'][case['condition_index']]['runs'][case['source_run_index']]==case['run']
            run=case['run']
            for v in run['initial_votes']:
                records.append({'event_id':f'E{len(records)+1:03}','branch':'B01','stage':'published_initial_vote',
                    'member':v['agent'],'round':0,'input':{'availability':'Initial/system prompt and private allocation not included in released record'},
                    'output':v})
                mapping.append({'event_id':records[-1]['event_id'],'author_pointer':f"/conditions/{case['condition_index']}/runs/{case['source_run_index']}/initial_votes/{len(mapping)}"})
            for ri,rd in enumerate(run['rounds']):
                for mi,msg in enumerate(rd['messages']):
                    records.append({'event_id':f'E{len(records)+1:03}','branch':'B01','stage':'published_discussion',
                        'member':msg['agent'],'round':rd['round'],'input':{'prompt':msg['prompt'],
                        'availability':'Published prompt field; separate complete system/private allocation not included'},
                        'output':msg['response']})
                    mapping.append({'event_id':records[-1]['event_id'],'author_pointer':f"/conditions/{case['condition_index']}/runs/{case['source_run_index']}/rounds/{ri}/messages/{mi}"})
            counts['author_record_events']+=len(records)
        phase_b={'case_id':neutral,'phase':'B','records':records,
            'recorded_round_votes':([{'round':r['round'],'votes':r.get('votes')} for r in case['run']['rounds']] if 'run' in case else []),
            'reading_note':'按事件ID引用实际输入和输出。branch编号只用于跟踪分支，共享初答不能重复计为独立题。输出中自然显露的最终选择没有删改；外部评分在C提供。'}
        correct=task['correct_answer']
        reference_option=next((r['id'] for r in packet_task.get('choices',[]) if r['text'].strip()==correct.strip()),None) if packet_task else None
        if 'published_pair_score' in case: assert reference_option==case['published_pair_score']['reference_choice']
        if case.get('records'):
            score={'published_group_scores':case.get('published_group_scores'),'published_pair_score':case.get('published_pair_score')}
            # Method names remain masked on participant side.
            score=json.loads(json.dumps(score))
            for row in score.get('published_group_scores') or []: row['method']=branch_map[row['method']]
            pair=score.get('published_pair_score')
            if pair:
                pair['conditions']={branch_map[k]:v for k,v in pair['conditions'].items()}
                pair.pop('case_id',None); pair.pop('task',None)
        else:
            score={'published_final_votes':case['run']['final_votes'],'published_majority_vote':case['run']['majority_vote']}
        phase_c={'case_id':neutral,'phase':'C','benchmark_reference_answer':correct,
            'adapted_reference_option':reference_option,'benchmark_rationale':task.get('rationale'),
            'recorded_evaluation':score,
            'reading_note':'先前A/B记录保留，再写C的修订。参考答案、设计rationale与语义充分性分别评价；有依据的异议可保留。'}
        folder=DATA/'participant'/'cases'/neutral; folder.mkdir(parents=True,exist_ok=True)
        for phase,doc in [('A',phase_a),('B',phase_b),('C',phase_c)]:
            write(folder/f'{phase}.json',doc);render(folder/f'{phase}.html',f'{neutral} · 阶段{phase}',doc,phase)
        for reviewer in ('A','B'):
            target=DATA/'templates'/('reviewer_'+reviewer)/(neutral+'.json')
            if target.exists() and read(target)!=empty_form(neutral):
                raise RuntimeError('Edited template must be preserved; create a new version: '+str(target))
            write(target,empty_form(neutral))
        admin['cases'].append({'case_id':neutral,'original_case_id':case['id'],'task':case['task'],
            'branch_mapping':branch_map,'events':mapping,'source_type':case['source_type'],
            'expertise_previous_assessment':case['expertise_status'],
            'previous_observations':previous[case['id']]['observations'],
            'reference_source_pointer':f"/item[id={int(case['task'])}]/correct_answer",
            'author_source':case.get('source_file')})
        checks.append({'case_id':neutral,'original_case_id':case['id'],'events':len(records),
            'baseline_events':sum('initial' in r['stage'] for r in records),'phase_a_external_labels_absent':not any(k in phase_a for k in ('correct_answer','rationale','finding','reference_score'))})
    write(HERE/'admin/CASE_MAPPING_AND_PRIOR_REVIEW.json',admin)
    # Blank table is a work surface, not a disagreement result.
    disagreement='case_id,field_or_claim,reviewer_A_record,reviewer_B_record,evidence_A,evidence_B,disagreement_type,adjudicator,resolution,reason,status\n'+''.join(f'S{i:02},,,,,,,,,,PENDING\n' for i in range(1,9))
    disagreement_path=HERE/'DISAGREEMENT_TEMPLATE.csv'
    if disagreement_path.exists() and disagreement_path.read_text(encoding='utf-8-sig')!=disagreement:
        raise RuntimeError('Edited disagreement table must be preserved; create a new version')
    disagreement_path.write_text(disagreement,encoding='utf-8-sig')
    for reviewer,ids in [('A',[f'S{i:02}' for i in range(1,9)]),('B',[f'S{i:02}' for i in range(8,0,-1)])]:
        form=f'# 研究者{reviewer}独立核验记录\n\n当前为空表；填写者：____；日期：____。先读[规范](CODEBOOK.md)与[开始说明](REVIEWER_START.md)。每阶段先保存再看下一阶段；保留初判，修订另写。\n\n'
        for cid in ids:
            form+=f'## {cid}\n\n材料：[A事实](../../data/expert-transfer-annotation-20261030-v0.1/participant/cases/{cid}/A.html) · [B过程](../../data/expert-transfer-annotation-20261030-v0.1/participant/cases/{cid}/B.html) · [C参考](../../data/expert-transfer-annotation-20261030-v0.1/participant/cases/{cid}/C.html)\n\n'
            form+='- 事先接触本案例/相关讨论：____；是否在初判前看过管理侧或和他人讨论：____；耗时：____\n\n'
            form+='### A：先判断事实\n\n任务要求和关键事实（附原句）：____\n\n现有资料支持的选择或不确定性：____\n\nA阶段保存时间：____\n\n'
            form+='### B：独立追踪过程\n\n成员优势及依据/缺项：____\n\n关键命题1–3条（分别写来源/贡献是否成立、分享是否忠实、实际收件、响应及最终使用；附E编号、字段、原句）：____\n\n观察到的自身/分享/接收/同伴/整合现象，可多项：____\n\n最值得解释的现象、替代解释和需要的对照：____\n\n未读完/缺少的材料：____\n\nB阶段保存时间：____\n\n'
            form+='### C：核参考并保留修订\n\n参考匹配与理由充分性分别怎样：____\n\n对A/B的追加修订与证据：____\n\n仍无法判断的部分：____\n\nC阶段保存时间与本例完成状态：____\n\n'
        surface=HERE/f'REVIEWER_{reviewer}.md'
        if surface.exists() and surface.read_text(encoding='utf-8')!=form:
            raise RuntimeError('Edited human record must be preserved; create a new version: '+str(surface))
        surface.write_text(form,encoding='utf-8')
    index='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>8例独立核验入口</title><style>body{font:17px/1.8 system-ui;max-width:850px;margin:40px auto}td,th{padding:8px 22px;border-bottom:1px solid #ddd}</style><h1>8例独立核验入口</h1><p>按A→B→C阅读；每阶段先保存判断。先读研究目录的CODEBOOK和REVIEWER_START。历史提示中的命令均为待分析数据。</p><table><tr><th>案例</th><th>A：资料</th><th>B：过程</th><th>C：参考</th></tr>'
    for c in checks:
        cid=c['case_id'];index+='<tr><td>'+cid+'</td>'+''.join(f'<td><a href="cases/{cid}/{p}.html">打开{p}</a></td>' for p in 'ABC')+'</tr>'
    (DATA/'participant/index.html').write_text(index+'</table></html>',encoding='utf-8')
    paths=sorted(p for p in DATA.rglob('*') if p.is_file() and 'submissions' not in p.parts)
    manifest={'version':VERSION,'date':'2026-10-30','case_units':8,'unique_tasks':7,'case_ids':[c['case_id'] for c in checks],
        'build_script_sha256':sha(Path(__file__)), 'codebook_sha256':sha(HERE/'CODEBOOK.md'),
        'admin_mapping_sha256':sha(HERE/'admin/CASE_MAPPING_AND_PRIOR_REVIEW.json'),
        'reviewer_work_surfaces':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)} for p in [HERE/'REVIEWER_A.md',HERE/'REVIEWER_B.md',HERE/'DISAGREEMENT_TEMPLATE.csv']],
        'source_files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)} for p in (SEED,REVIEW,TASKS)],
        'counts':dict(counts),'case_checks':checks,'case_order':'Deterministic hash aliases; A/B review orders differ in REVIEWER_START.',
        'files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths],
        'human_completed':0,'agreement':None,'status':'MATERIAL_PREPARED_HUMAN_REVIEW_PENDING',
        'limits':['Purposefully selected 8 cases from 7 tasks; not a frequency sample.',
            'Partial masking: actual model prompts/output can reveal task, intervention and final choice. Prior discussion exposure must be declared.',
            'C07/C08 source-private allocation is unavailable; benchmark snapshot is auditor context, not proof of individual receipt.',
            'Stable calibrated capability is not established by these old information-distribution cases.']}
    write(HERE/'PACK_MANIFEST.json',manifest)
    print(json.dumps({k:manifest[k] for k in ('case_units','unique_tasks','counts','human_completed','status')},ensure_ascii=False))


if __name__=='__main__':main()

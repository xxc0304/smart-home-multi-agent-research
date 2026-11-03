"""Literal pointers + declared analyst notes. This script does not infer mechanism labels."""
from pathlib import Path
from collections import Counter
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
SEED=ROOT/'research/expert-team-assets-20261029/CASE_SEED_8.json'
TASKS=ROOT/'data/task-source-audit-20261021/hiddenbench.json'


def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def get(value,parts):
    for key in parts:value=value[int(key)] if isinstance(value,list) else value[key]
    return value
def leaves(value,path=()):
    if isinstance(value,dict):
        for k,v in value.items():yield from leaves(v,path+(k,))
    elif isinstance(value,list):
        for k,v in enumerate(value):yield from leaves(v,path+(k,))
    elif isinstance(value,str):yield path,value


def main():
    seed=read(SEED); tasks={int(r['id']):r for r in read(TASKS)}
    cases={c['id']:c for c in seed['cases']}; events=[]
    def add(cid,parts,fragment,note):
        ci=next(i for i,c in enumerate(seed['cases']) if c['id']==cid)
        value=get(cases[cid],parts)
        assert isinstance(value,str) and fragment in value,(cid,parts,fragment)
        offset=value.index(fragment); excerpt=value[max(0,offset-50):offset+len(fragment)+100]
        item={'id':f'E{len(events)+1:02}','case_id':cid,'seed_pointer':'/cases/'+str(ci)+'/'+ '/'.join(str(p) for p in parts),
              'literal_quote':fragment,'context_excerpt':excerpt,'analyst_note':note}
        if parts[0]=='records':
            record=cases[cid]['records'][parts[1]]
            item.update({'slot':record['row']['slot'],'source_raw':record['raw_path'],'raw_sha256':sha(ROOT/record['raw_path'])})
            assert json.loads(record['raw_text'])=={k:v for k,v in record['row']['answer'].items() if k in json.loads(record['raw_text'])}
        else:
            item['source_file']=cases[cid]['source_file']
            source=read(ROOT/item['source_file'])
            assert source['conditions'][cases[cid]['condition_index']]['runs'][cases[cid]['source_run_index']]==cases[cid]['run']
        events.append(item)
    def local(cid,slot,path,fragment,note):
        ri=next(i for i,r in enumerate(cases[cid]['records']) if r['row']['slot']==slot)
        base=['records',ri]+path
        value=get(cases[cid],base)
        if not isinstance(value,str):
            matches=[(p,t) for p,t in leaves(value) if fragment in t]
            assert matches,(cid,slot,fragment)
            base+=list(matches[0][0])
        add(cid,base,fragment,note)
    def author(cid,round_number,member_index,field,fragment,note):
        ri=next(i for i,r in enumerate(cases[cid]['run']['rounds']) if r['round']==round_number)
        add(cid,['run','rounds',ri,'messages',member_index,field],fragment,note)

    local('C01',2,['packet','information_available'],'meeting their usual requirements for a deal of this size','A2所持原始资料支持共同投资条件已满足')
    local('C01',10,['packet','messages_from_other_participants'],'PRIVATE.A2 resolves Skylake\'s only stated blocker','A1该次输入真实包含关键报告')
    local('C01',10,['row','answer','reasoning'],'A3 correctly notes A2\'s PRIVATE.A2 is absent from the packet and cannot be credited','报告实际在收件中，却按原件可见性拒绝')
    local('C01',10,['row','answer','reasoning'],'A1\'s regulatory/bank-hold claim is in the packet as information_available, so it is data to weigh, not necessarily verified fact','A1也降低自己直接事实的权重，机制不只是别人不可信')
    local('C01',11,['row','answer','reasoning'],'PRIVATE.A2, present in the packet, confirms Skylake\'s sole blocker','A2仍保留参考选择，不能把整队写成全员改错')
    local('C01',14,['row','answer','reasoning'],'close within the 12-hour window','把选择期限与成交时间合并的表述须与原题要求区分')
    local('C02',17,['packet','information_available'],'The main highway to Gemini is temporarily closed for repairs','原文是主公路，不是全部可行路径')
    local('C02',17,['row','answer','reasoning'],'the only viable route is closed','初次独立输出已经加强道路范围')
    local('C02',19,['packet','information_available'],'fully restored functionality a few hours later','A3原资料包含恢复运行')
    local('C02',19,['row','answer','reasoning'],'Nova is newly renovated but has little emergency experience and a recent outage','初答遗漏恢复状态，并把停电保留为负面考虑')
    local('C02',20,['row','answer','reasoning'],'PUBLIC.1 indicates the only viable route is closed','自有PRIVATE道路事实在输出中错归公共条目')
    local('C02',21,['packet','messages_from_other_participants'],'Gemini is likely unreachable because the only viable route is closed','A2收到报告，但报告本身带范围加强')
    local('C02',21,['row','answer','reasoning'],"A1's route-closure claim is unsupported",'接收者拒绝来源报告')
    local('C02',29,['row','answer','reasoning'],'Atlas is the safest viable choice','新增：理由结论推荐Atlas')
    local('C02',29,['raw_text'],'"choice": "option_1"','新增：同一输出的结构化选择为Gemini')
    local('C03',41,['packet','information_available'],'Cape Industries: (h) N','A4自身资料已有成本失败项')
    local('C03',41,['row','answer','reasoning'],'Cape fails only (g) among known criteria','A4初答漏掉自有h失败，不是讨论后才出错')
    local('C03',55,['packet','information_available'],'Cape Industries: (h) N','A2自己持有成本失败项')
    local('C03',55,['row','answer','reasoning'],'Cape fails (h) cost and (f) weight, central criteria','A2输出仍承认失败项')
    local('C03',55,['row','answer','reasoning'],"I follow A1's stronger-supported reading: Cape",'A2追随A1，而非简单服从多数')
    local('C03',56,['row','answer','reasoning'],"A1's claim that Starlight's (f)/(i) data is unsupported is false",'A3明确反驳且保留参考答案，构成反例')
    local('C03',45,['row','answer','reasoning'],'Choosing Starlight maximizes coordination and correctness','A4从错误初答改向参考答案，同伴可有益')
    local('C04',29,['row','answer','reasoning'],"Eddie's alibi is unverified",'A2在原件路由第一轮形成参考候选')
    local('C04',32,['row','answer','reasoning'],'Mickey had motive','A2下一轮由参考候选回到Mickey')
    local('C04',32,['row','answer','reasoning'],'lied about going to pick Guion up','推断中的说谎被当确定前提，原文仅说改变行程')
    local('C04',37,['row','answer','reasoning'],'Mickey best fits means, motive, and opportunity','全信息单体也输出非参考候选')
    local('C05',3,['packet','own_sources'],'The guilty person is less than 30 years old','有效年龄约束的直接来源')
    local('C05',1,['row','answer','text'],'Mr. X (53) is excluded by the age restriction','局部稿正确给出排除后果')
    local('C05',4,['packet','local_reconstruction'],'Mr. X is 53 (incompatible)','排除后果真实进入最终接收者输入')
    local('C05',4,['row','answer','reasoning'],'A2 itself concedes age compatibility is not evidence of guilt','把局部约束不足以定案作为弱化它的理由')
    local('C05',4,['row','answer','reasoning'],'A2\'s age constraint would also exclude Mr. X (53)','最终输出明确承认对所选对象的排除')
    local('C05',4,['row','answer','reasoning'],'it cannot override the more specific vehicle/alcohol profile','按来源和叙事具体性排序，而未兑现排除约束')
    local('C05',4,['packet','historical_work'],'described only as a passenger','乘客假设在历史稿中已存在')
    local('C05',4,['packet','shared_contributions','A3','facts'],'passenger','结构化字段也含该推断，不只是自由文本')
    local('C05',4,['request_payload','instructions'],'Shared contributions and execution reports are fallible reports','当前实验提示显式区分原件与他人报告；解释须考虑协议设计')
    local('C06',27,['packet','own_sources'],'The only access road to Lakeview Resort is closed','唯一通路范围是直接来源事实')
    local('C06',25,['row','answer','text'],"The historical_work's suggestion that \"one blocked route does not prove all routes blocked\" is not supported by S01's wording",'可见旧稿的局部重建直接指出旧推断问题')
    local('C06',27,['row','answer','text'],'not a confirmed, region-wide, or venue-wide closure','隔离局部稿主要报告范围和不确定性')
    local('C06',26,['row','answer','reasoning'],"historical_work's caveat that 'one blocked route does not prove all routes blocked' is unsupported",'参考命中分支明确重算旧推断')
    local('C06',26,['row','answer','reasoning'],'categorical obstacle for the scheduled time','其时间确定性表述比expected更强')
    local('C06',28,['row','answer','reasoning'],'it does not establish that the venue itself is closed or that no alternative route exists','另一分支再次把唯一通路淡化成可能另有路径')
    local('C06',28,['row','answer','reasoning'],"does not overturn the historical work's tentative selection of Lakeview",'仍保留旧稿选项，旧稿在最终两分支均可见')
    author('C07',2,0,'response','the blocked South Street access','正确的受阻陈述出现在公开对话')
    author('C07',2,1,'prompt','the blocked South Street access','该句真实进入下一成员prompt')
    author('C07',2,1,'response','South Street remains open to vehicles','收到后仍给相反陈述')
    author('C07',2,3,'response','South Street is confirmed open','后续陈述使用confirmed语气')
    author('C07',3,0,'response','With South Street confirmed open','原阻断报告者后续也改为开放')
    author('C08',1,1,'response','Fact 3 explicitly states its basement has flooded','同名编号指向Blue River洪水事实')
    author('C08',1,2,'response',"Fact 3 refers to Oakridge Library's incomplete roof",'另一个成员把同名编号用于屋顶旧信息')
    author('C08',1,3,'response',"Fact 3, which explicitly confirms Oakridge Library's new roof is structurally sound and safe",'又一同名编号指向屋顶通过检查')
    author('C08',1,3,'response','we must direct residents there immediately','参考候选在第1轮已由Person4提出，早于EOC声明')
    author('C08',2,1,'response',"Blue River Community Center's basement flooded an hour ago",'成员进一步给出原句，而不是所有事实都未共享')
    author('C08',2,2,'response','different, dangerously conflicting sets of information','不同材料被统称危险冲突，需区分事实是否真互斥')
    author('C08',3,3,'response','I am contacting the Emergency Operations Center','声称发起外部核验')
    author('C08',5,3,'response',"I have the EOC's unified report",'声称收到报告，发布记录无单独工具回执字段')
    author('C08',6,0,'response','Thank you for that definitive report','成员将该声明作为definitive依据')

    structural={}; transitions={}
    for cid,slots in [('C05',(2,4)),('C06',(26,28)),('C04',(29,32))]:
        a,b=[next(r for r in cases[cid]['records'] if r['row']['slot']==v) for v in slots]
        structural[cid]={'slots':list(slots),'packet_different_keys':sorted(k for k in a['packet'].keys()|b['packet'].keys() if a['packet'].get(k)!=b['packet'].get(k)),
            'request_payload_different_keys':sorted(k for k in a['request_payload'].keys()|b['request_payload'].keys() if a['request_payload'].get(k)!=b['request_payload'].get(k)),
            'instruction_prefix_same':a['request_payload']['instructions'].split('PACKET=',1)[0]==b['request_payload']['instructions'].split('PACKET=',1)[0],
            'history_present_in_both':all('historical_work' in r['packet'] for r in (a,b)),
            'history_same':a['packet'].get('historical_work')==b['packet'].get('historical_work')}
        if cid=='C04':structural[cid]['messages_source_only']=all(set(m)=={'ref','content'} for m in b['packet']['messages_from_other_participants'])
    assert structural['C05']['packet_different_keys']==['local_reconstruction']
    assert structural['C06']['packet_different_keys']==['local_reconstruction']
    assert all(structural[c]['instruction_prefix_same'] and structural[c]['request_payload_different_keys']==['instructions'] for c in ('C05','C06'))
    assert structural['C04']['packet_different_keys']==['previous_answer'] and structural['C04']['messages_source_only']
    for cid in ('C01','C02','C03','C04'):
        case=cases[cid]; correct=tasks[int(case['task'])]['correct_answer']
        choices=case['records'][0]['packet']['task']['choices']
        reference=next(v['id'] for v in choices if v['text']==correct)
        groups={}
        for r in case['records']:
            key=f"{r['row']['method']}_r{r['row']['round']}"
            groups.setdefault(key,[]).append(r['row']['answer']['choice'])
        transitions[cid]={'reference_option':reference,'member_matches':{k:{'n':len(v),'matching_reference':sum(c==reference for c in v),'choices':v} for k,v in groups.items()}}
    a1=next(r for r in cases['C02']['records'] if r['row']['slot']==29)
    assert a1['row']['answer']['choice']=='option_1' and 'Atlas is the safest viable choice' in a1['row']['answer']['reasoning']
    proof={'type':'assistant_qualitative_analysis','date':'2026-10-30','case_units':8,'unique_tasks':7,
        'source_files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)} for p in (SEED,TASKS)],
        'literal_evidence_items':len(events),'events':events,'structural_comparisons':structural,'reference_choice_transitions':transitions,
        'new_model_calls':0,'human_annotations':0,
        'scope':'Literal checks and declared assistant interpretations; not human independent labels, prevalence or causal effects.'}
    (HERE/'EVIDENCE.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md='# 逐字证据与原件定位\n\n2026-10-30。下列注释为助手分析，quote为程序核对的原始字面内容。C编号沿用旧案例；这里的E编号属于本报告，不与核验包的事件E编号混用。\n\n'
    for item in events:
        md+=f"<a id=\"{item['id'].lower()}\"></a>\n\n## {item['id']} · {item['case_id']}\n\n"
        md+=f"{item['analyst_note']}\n\n> {item['literal_quote']}\n\n"
        if 'source_raw' in item:md+=f"[原始回复](../../{item['source_raw']})；slot {item['slot']}；"
        else:md+=f"[作者原文件](../../{item['source_file']})；"
        md+=f"[摘录JSON](../expert-team-assets-20261029/CASE_SEED_8.json) pointer `{item['seed_pointer']}`。\n\n"
    (HERE/'EVIDENCE.md').write_text(md,encoding='utf-8')
    print(json.dumps({'literal_items':len(events),'structural_comparisons':structural,'choice_transitions':transitions},ensure_ascii=False))


if __name__=='__main__':main()

"""Persist assistant judgments and build a reversible training-use candidate.

Judgments are explicit editorial records, not automatic semantic detection.
Original T/V/C/D/H exports remain unchanged. No models or training are run.
"""
from pathlib import Path
from collections import Counter
import json
import hashlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# case, verdict, references, full candidate context read, finding
JUDGMENTS = [
 ('D01','SUPPORTED_QUALIFIED',[17,15],True,'P17含Yale与Miami两处任职；Yale Law School→1843可由P15支持，但雇主未限定时期。保留答案，记录指代限制。'),
 ('D02','UNSUPPORTED_BRIDGE',[6,5,10],True,'P6 owner为Virgin Group；P5谈Virgin Games在英国经营及品牌许可，不明确支持Virgin Group所属国家。P10支持英国地理部分；标注桥接不能视为已给定。'),
 ('D03','SUPPORTED_QUALIFIED',[0,18],True,'P0给Gary Allan；P18给Hillary Lindsey伴唱但不再次写Gary Allan。按歌曲名可直接找到答案，不能据答对证明使用完整链。'),
 ('D04','SUPPORTED',[5,17],True,'Artsvanik→Syunik Province→Kapan两关系明确。问句capitol视为可理解拼写，不改题。'),
 ('D05','SUPPORTED_QUALIFIED',[6,8,14],True,'Gatsby→Long Island→New York可接；P14明确赠送者people of France。实际文字受赠者为美国人民，问句称给州是宽泛表达；答案仍有支持，也存在只读Statue段捷径。'),
 ('D06','SUPPORTED_QUALIFIED',[18,16],True,'P18写Yves Bouvier于2009迁居Singapore；P16写新加坡任命方式。from若指居住地可接，不能当作已证明出生地；仅按给定旧文本核读，不作现行法律建议。'),
 ('D07','SUPPORTED',[17,16],True,'P17明确美国首店Iowa；P16明确Iowa入联法案由James K. Polk签署。1846州成立而非1976首店开业时间。'),
 ('D08','SUPPORTED_QUALIFIED',[12,4],True,'P12称该片为Hong Kong film，P4写香港货币。一般地域指代支持答案；若based in专指剧情地点，则P12未明确交代。保留评分，不扩大成无条件剧情推断。'),
 ('T01','UNSUPPORTED_BRIDGE',[9,7],True,'P9演出者Jerry Lee Lewis，P7仅Waylon Payne个人资料，未给电影Walk the Line扮演关系；全文P12/P15是歌曲I Walk the Line，不能补该关系。'),
 ('T02','SUPPORTED_QUALIFIED',[3,0],False,'The Colbys→ABC、比赛由ABC播出关系明确；直接看节目标题/正文也可能答出，不能保证监督完整组合。'),
 ('T03','SUPPORTED_QUALIFIED',[3,15],False,'歌曲由Lou Rawls演唱，1962专辑由Capitol发行有支持；未限定时期的belong to不应被扩成其唯一/现任厂牌。'),
 ('T04','ENTITY_CONFLICT',[14,5,11],True,'P14出生Jackson County, Florida；P5县法院在Jacksonville, Oregon；P11统计来自Jacksonville, Florida。同名县/城市跨州错接，不是有效同实体链。'),
 ('T05','SUPPORTED',[5,0],False,'Barnas Sears毕业Brown，James Manning为Brown创办者之一；问题未要求唯一创办人，one of founders足够支持。'),
 ('T06','SUPPORTED',[13,8],False,'P13职位由King George III创设；P8虽标题Queen Victoria，正文明确George III死于1820。标题不同不等于错标。'),
 ('T07','SUPPORTED',[5,7],False,'P5 performer兼作者Mariah Carey；P7明确她与Nicki Minaj都在一季后离开评委席。作者还有Walter，问句performer限定了目标。'),
 ('T08','SUPPORTED',[18,2],False,'学校位于Santa Rosa，P2明确2016估计人口175155；按给定年代数据支持，不将此数当当前人口。'),
 ('T09','RELATION_CONFLICT',[16,4],True,'Burtts Corner→New Brunswick无问题；P4说Rivière-Verte在Edmundston东南15公里，因此Edmundston在Rivière-Verte西北。组合问句要其东南，方向倒置，且15公里不证明接壤。'),
 ('T10','SUPPORTED_QUALIFIED',[0,3],False,'Lan Xing出生四川；P3明确Qu Neng受令repel assault into Sichuan。问句force assault措辞不自然，应按上下文抵御入侵理解，不能改成他发动入侵。'),
 ('T11','SUBJECT_CONFLICT',[11,19],True,'P11 preacher为Eric Clapton；P19学习guitar/mandolin/violin的主语是Stevie Blacke，Eric仅为其听的音乐。不能推出Eric演奏violin；本轮不凭常识替换gold为guitar。'),
 ('T12','SUPPORTED_QUALIFIED',[6,0],False,'P6将首次记录归NYT，P0列NYT 1851。按该归属可得参考答案；first recorded use不等于证实发明者，originator表达宽泛，保留限制不作硬错误。'),
]


def main():
    packet=json.loads((HERE/'CASE_PACKET_GOLD_SIDE.json').read_text(encoding='utf-8'))
    lookup={c['case']:c for c in packet['cases']}
    assert set(lookup)=={r[0] for r in JUDGMENTS} and len(JUDGMENTS)==20
    records=[]
    for label,verdict,refs,full,note in JUDGMENTS:
        case=lookup[label]
        assert set(refs)<={p['idx'] for p in case['input']['paragraphs']}
        records.append(dict(case=label,task_id=case['input']['id'],role=case['role'],
            question=case['input']['question'],reference_answer=case['target']['answer'],
            verdict=verdict,evidence_paragraphs=refs,full_context_read=full,
            review_scope='full candidate context and labeled support' if full else 'question/decomposition/labeled support',
            finding=note,reviewer='main_assistant',independent_human_label=False))
    bad=[r['task_id'] for r in records if r['role']=='T' and r['verdict'] in
         ('UNSUPPORTED_BRIDGE','ENTITY_CONFLICT','RELATION_CONFLICT','SUBJECT_CONFLICT')]
    assert len(bad)==4
    source=ROOT/'data/expert-training-20261030-v1/train.messages.jsonl'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    all_rows=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
    kept=[r for r in all_rows if r['id'] not in bad]
    assert len(all_rows)==1800 and len(kept)==1796
    candidate=ROOT/'data/expert-training-20261031-review-candidate'
    candidate.mkdir(parents=True,exist_ok=True)
    with (candidate/'train.messages.jsonl').open('w',encoding='utf-8') as out:
        for row in kept:out.write(json.dumps(row,ensure_ascii=False)+'\n')
    overlay=dict(date='2026-10-31',status='REVIEW_CANDIDATE_NOT_ACTIVATED_NOT_TRAINED',
        original_training=str(source.relative_to(ROOT)),original_n=1800,proposed_n=1796,
        excluded_known_issue_ids=bad,selection_basis='Fixed-prefix text evidence, no model scores; only explicit bridge/entity/relation/subject issues excluded.',
        candidate_messages=str((candidate/'train.messages.jsonl').relative_to(ROOT)),
        validation_inputs='data/expert-training-20261030-v1/validation.inputs.jsonl',
        validation_targets='data/expert-training-20261030-v1/validation.targets.jsonl',
        limitations=['1796 is a known-issue-filtered candidate, not a fully audited clean dataset.',
                    'Source T/V/C/D/H assignments and official scoring unchanged; no excluded rows recycled into evaluation.',
                    'Only 12 training rows semantically examined; no corpus-wide defect rate inferred.',
                    'Use requires recording this candidate in the eventual run contract; active v0.5 not silently switched.'])
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    (candidate/'USE_MANIFEST.json').write_text(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result=dict(date='2026-10-31',kind='ASSISTANT_TEXT_REVIEW_NOT_MODEL_RESULTS',
        independence='none',D_n=8,T_n=12,full_context_cases=sum(r['full_context_read'] for r in records),
        verdict_counts_by_role={role:dict(Counter(r['verdict'] for r in records if r['role']==role)) for role in ('D','T')},
        records=records,training_use_overlay=overlay,experimental_model_calls=0,training_runs=0,
        limits='Fixed prefixes are not representative prevalence estimates; no human independent annotation performed.')
    (HERE/'REVIEW_RECORDS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(D_n=8,T_n=12,counts=result['verdict_counts_by_role'],
                         full_context_cases=result['full_context_cases'],candidate_n=1796,active_source_unchanged=True)))


if __name__=='__main__':main()

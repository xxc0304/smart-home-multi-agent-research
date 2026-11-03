"""Offline paired semantic review. No model client, network call, or rescore."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/hb-local-contribution-live-20261025-r1"
PREPARED = ROOT / "runs/hb-local-contribution-prepared-20261025-r1"

# All 32 member pairs, manually read in full at final delivery. The cue only
# extracts a traceable excerpt; it is not an automatic semantic scoring rule.
PAIRS = [
("005",1,"A1",3,12,"fundraising","共同纠正Stevens募款归属；普通组保留总体推荐，提问组改成条件性筹款比较。两组均未展开Roberts的人脉与公益服务。"),
("005",1,"A2",5,14,"innovative","两组都提出Stevens压制创新。提问组另外明确提出Roberts的倾听/合作领导记录，普通组遗漏；这是明确的新增内容差异。"),
("005",1,"A3",7,16,"fundraising","两组都纠正募款并提出饮酒风险；提问组更聚焦两个标准。两组都未利用本人的Roberts教学和科研改善记录。"),
("005",1,"A4",9,18,"innovative","两组都提出Stevens创新/品行问题；提问组将重点转向公共材料的募款归属。两组都漏掉本人的Roberts拨款与多样性实绩。"),
("005",2,"A1",31,22,"fundraising","两组都纠正Stevens募款；提问组限定于筹款标准，普通组还使用Jones领导风险。没有新增独有事实。"),
("005",2,"A2",33,24,"innovative","两组都有Stevens创新反证；提问组主要重审公共筹款归属，两组均未展开本人掌握的Roberts合作风格。"),
("005",2,"A3",35,26,"fundraising","两组交付同样的筹款纠正/品行风险，均未展开Roberts教学与科研实绩；条件性筹款门槛不等于任务已给定的权重。"),
("005",2,"A4",37,28,"innovative","提问组在主结论中提及Roberts多样性，普通组仅在missing的例外说明中承认该记录；两组均未处理数百万拨款。"),
("009",1,"A1",50,41,"oxygen","两组都排除C的当前重症救治能力，并有条件偏向B；没有新增知识差异。"),
("009",1,"A2",52,43,"main road","两组都指出B主路中断。普通组进一步建议先向C出发再确认路况，提问组保留A/C未决，后者的行动边界更清楚。"),
("009",1,"A3",54,45,"pass","两组都修正A山口风险。提问组不选总答案，普通组有条件保留B；普通组的条件比较不能因全局参考为A就判错。"),
("009",1,"A4",56,47,"beds","两组都提出B无当前床位。普通组询问C救护车能否跨越洪水路段，提问组设想B床位可释放；二者均未确认这些可能性，无明确单向质量优势。"),
("009",2,"A1",60,69,"oxygen","两组都排除C；提问组更干净地停在局部结论，普通组对B的偏好仍保留未知条件。"),
("009",2,"A2",62,71,"landslide","两组都区分主路封闭与所有通路不可达，保留替代路线未知；核心事实及边界接近。"),
("009",2,"A3",64,73,"pass","两组都修正A的道路前提，但均将B拥有大型ICU扩张为confirmed ICU capacity。提问组还对A的最新清通更苛刻；提问未消除此推理缺口。"),
("009",2,"A4",66,75,"beds","两组均撤回B当前接收能力已成立的判断，并只在床位恢复等条件下保留B；无独有新增知识。"),
("012",1,"A1",79,88,"Green Valley","两组都正确引入游客关闭不适用于紧急疏散的例外；提问组不再单选Blueberry，普通组的局部偏好仍有条件。"),
("012",1,"A2",81,90,"sinkhole","两组都排除Red Lake唯一道路；提问组停止额外排名，普通组有条件比较其余两点。主要事实相同。"),
("012",1,"A3",83,92,"power","两组都用断电/步行限制否定Blueberry，并有条件偏向Red Lake。该局部偏好不能按其未见的其他成员资料判错；最终整合撤回了Red Lake。"),
("012",1,"A4",85,94,"bridge","两组都有Blueberry车辆通路中断；提问组保留未确认替代路线，普通组推荐Red Lake但附路况条件。没有新的事实发现。"),
("012",2,"A1",107,98,"Green Valley","两组都提出紧急疏散例外。提问组反复要求原件的签发人/文件/时效确认，更保守但未带来新的可用事实。"),
("012",2,"A2",109,100,"sinkhole","两组都排除Red Lake，再对Blueberry作局部条件偏好；增补内容接近。"),
("012",2,"A3",111,102,"power","两组都交付断电/步行约束，并有条件偏向Red Lake，核心相同。"),
("012",2,"A4",113,104,"bridge","提问组保留车辆不可达这一明确后果；普通组将给定桥塌报告改成未核实前只降级。提问组的约束表达更直接，但两组最终都选择Green Valley。"),
("023",1,"A1",126,117,"road","两组都交付Lakeview唯一道路关闭。提问组额外悬置次级道路/班车/临时通路，来源未给这些可行性；普通组的图书馆偏好仍明确待确认。"),
("023",1,"A2",128,119,"phone","两组都提供电话接受临时预订的例外，并保留实际预订未确认；无新增独有事实。"),
("023",1,"A3",130,121,"catering","两组都交付图书馆禁止餐饮。提问首轮主要围绕Lakeview具体日期/室内条件，最终才同时交付本人禁餐信息；没有体现更早发现独特知识。"),
("023",1,"A4",132,123,"mosquito","两组都交付蚊虫滋扰信息，却均不同程度将室内/防护备用空间升为必要条件；提问本身没有防止任务要求扩张。"),
("023",2,"A1",136,145,"road","两组都排除Lakeview。普通组暂优先联系酒店，提问组保留酒店/图书馆未决，均未确认最终预订。"),
("023",2,"A2",138,147,"phone","两组都纠正酒店通知期限并保留电话预订待确认；核心及边界一致。"),
("023",2,"A3",140,149,"catering","两组都交付图书馆禁餐。提问组更强调没有场地已完整确认，但没有普通组缺少的关键私有事实。"),
("023",2,"A4",142,151,"mosquito","两组都将蚊虫风险连接到室内/遮蔽空间确认；提问组把protected capacity称为decisive gap，依然有把偏好升为硬要求的风险。"),
]

ROBERTS_FACTS = [
("R1","A1.S1","影响力联系人脉"),
("R2","A1.S1","住房/人权非营利机构志愿服务"),
("R3","A2.S1","善于倾听、合作决策的领导记录"),
("R4","A3.S1","学生与同事认可其教学"),
("R5","A3.S1","任院长期间科研生产率提高"),
("R6","A4.S1","任院长期间提高教师多样性"),
("R7","A4.S1","为非营利机构争取数百万美元联邦拨款"),
]

# Exhaustive manual presence labels for this seven-fact diagnostic subset in the
# four final integration rationales, not weights or requirements for a good answer.
COVERAGE = {
10: {},
19: {"R3":"collaborative decision-making references","R4":"excellent teaching","R6":"increased faculty diversity as dean"},
29: {"R3":"collaborative style","R4":"teaching praise","R6":"diversity gains"},
38: {},
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clip(text, cue):
    start=text.lower().index(cue.lower())
    return text[max(0,start-100):min(len(text),start+230)]


def main():
    rows=read(RUN/"progress.json")["rows"]
    byslot={r["slot"]:r for r in rows}
    assert len(rows)==152 and all(r["status"]=="readable" for r in rows)
    manifest=read(PREPARED/"manifest.json")
    assert digest(PREPARED/"manifest.json")=="2a01a0dfdcaa45bfdbbf940523cd9b437cf61c606784d4754c9c0f02ecb62093"
    for rel,sha in manifest["files"].items():
        assert digest(PREPARED/rel)==sha
    for rel,sha in manifest["code_sha256"].items():
        assert digest(RUN/"frozen_source"/rel)==sha

    annotations=[]
    for task,rep,member,oslot,qslot,cue,note in PAIRS:
        sides={}
        for method,slot in (("ordinary",oslot),("local_question",qslot)):
            r=byslot[slot]
            assert (r["task"],r["repeat"],r["member"],r["stage"],r["method"])==(f"hb-local-dev-{task}",rep,member,"second",method)
            a=r["answer"]
            sides[method]=dict(final_slot=slot,first_slot=slot-1,raw_sha256=digest(RUN/f"{slot:03d}.raw.txt"),
                               core_fact_excerpt=clip(a["conclusion"],cue),
                               own_source_disclosed=any(e["source"]==member+".S1" for e in a["evidence"]))
        annotations.append(dict(task=task,repeat=rep,member=member,
                                shared_primary_local_fact=True,
                                label_basis="Manual whole-final-delivery review; excerpt extraction is only traceability.",
                                paired_note=note,**sides))
    assert len(annotations)==32

    evidence_pairs=[]
    for task in ("005","009","012","023"):
        for rep in (1,2):
            rs=[r for r in rows if r["task"]==f"hb-local-dev-{task}" and r["repeat"]==rep and r["stage"]=="integrate"]
            packets={}
            for r in rs:
                request=read(RUN/"actual_requests"/f"{r['slot']:03d}.json")
                packets[r["method"]]=json.loads(request["instructions"].split("PACKET=",1)[1])
            o,q=packets["ordinary"],packets["local_question"]
            assert o["disclosed_evidence"]==q["disclosed_evidence"]
            private=[e["ref"] for e in o["disclosed_evidence"] if e["ref"].startswith("A")]
            assert private==["A1.S1","A2.S1","A3.S1","A4.S1"]
            evidence_pairs.append(dict(task=task,repeat=rep,identical_disclosed_originals=True,
                                       private_originals=private,final_slots={r["method"]:r["slot"] for r in rs}))

    coverage=[]
    for slot,present in COVERAGE.items():
        r=byslot[slot];reason=r["answer"]["reasoning"]
        for text in present.values():
            assert text in reason
        assert "grant" not in reason.lower()
        coverage.append(dict(slot=slot,method=r["method"],repeat=r["repeat"],choice=r["answer"]["choice"],
                             facts_present=list(present),fact_excerpts=present,focused_fact_coverage=f"{len(present)}/7",
                             absent_fact_labels=[fid for fid,_,_ in ROBERTS_FACTS if fid not in present]))
    source=read(PREPARED/"contexts/hb-local-dev-005/A4.json")["own_sources"][0]["content"]
    assert "Instrumental in securing a multimillion dollar federal grant" in source
    assert "thoughtful listener using collaborative decision-making" in byslot[14]["answer"]["conclusion"]
    assert "Roberts' faculty-diversity record" in " ".join(byslot[37]["answer"]["missing"])
    assert "documented diversity gains" in byslot[28]["answer"]["conclusion"]
    for slot in (64,73):
        assert "confirmed ICU capacity" in byslot[slot]["answer"]["conclusion"]

    data=dict(
        procedure="Offline, same assistant, posthoc and nonblind semantic review. All 64 final deliveries and 32 pair comparisons reviewed; selected first-stage transitions checked. No independent annotation agreement claim.",
        scope="No new requests or outcome rescoring. The original frozen reference scores remain 6/8 versus 6/8.",
        source_manifest_sha256=digest(PREPARED/"manifest.json"),
        pairs=annotations,identical_original_evidence_pairs=evidence_pairs,
        primary_fact_overlap="32/32 member pairs convey the same central local fact; this does not certify every extra claim.",
        positive_candidate_signal=dict(task="005",description="Both question-arm integration rationales explicitly include Roberts collaboration, teaching and diversity positives; neither ordinary-arm rationale includes these seven diagnostic positives.",integrations=coverage),
        roberts_positive_fact_legend=[dict(id=fid,source=src,description=desc) for fid,src,desc in ROBERTS_FACTS],
        missing_grant=dict(provider_final_slots=[9,18,28,37],integration_slots=[10,19,29,38],
                           source="A4.S1",original_excerpt="Instrumental in securing a multimillion dollar federal grant",
                           observation="All four A4 final conclusions and all four integration rationales omit this record. The raw source was disclosed to all integrations."),
        limitations=[
            "The seven-fact subset is an exploratory coverage diagnostic, not a general answer-quality score or a requirement to list every positive fact.",
            "New mentions in an integration may be extracted from disclosed originals rather than caused by a member's question or summary.",
            "Identical original evidence could make the final integrator compensate for local contribution differences; no source-only or contribution-only intervention isolates this cause.",
            "Local alternative recommendations are judged using their visible knowledge and conditions, not other members' hidden facts.",
            "Questions about unverified alternatives are not treated as asserted false facts; attention cost and hard-constraint expansion are discussed separately.",
            "Four development tasks with two repetitions do not provide broad generalization or independent statistical samples.",
        ],
        decision="Retain the repeated rationale-coverage signal. Do not promote explicit self-questioning alone as a demonstrated accuracy mechanism, and do not discard it as useless. The next design target is selection and comparative use of distinctive evidence, with the existing ordinary-contribution baseline kept intact."
    )
    (RUN/"PAIRED_CONTRIBUTION_REVIEW.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=[
        "# 四任务局部贡献逐对复核",
        "",
        "本次纯离线分析，新增模型请求0。逐一阅读64份最终成员交付，完成32组配对复核，并检查相关首轮及16份整合答案。标注由同一助手事后非盲完成；不声称独立盲评或标注一致性。原始6/8对6/8的参考命中分数不变。",
        "",
        "## 结论",
        "",
        "有一个重复的过程正信号：005中提问组两份整合理由均覆盖Roberts的合作、教学和多样性记录，普通组均未覆盖。最终选择仍相同；这支持保留候选机制，尚不支持最终准确率增益。",
        "",
        "32组成员配对均交付了相同的主要局部事实。提问改变了表达方式，部分交付边界更清楚，也产生了无必要的额外条件，并未稳定生成普通组缺少的关键事实。两组所有整合请求都披露了相同的四份完整私有原件，事实可见范围8/8完全一致。整合者有机会独立从原件补出、修正成员摘要，因此本批主要测到同资料整合时的贡献表述影响。",
        "",
        "## 保留下来的正面差异",
        "",
        "| 005重复 | 普通组对Roberts七项正面资料的理由覆盖 | 提问组 | 最终选择 |",
        "|---|---:|---:|---|",
        "| 1 | 0/7（槽10） | 3/7（槽19） | 两组O1 |",
        "| 2 | 0/7（槽38） | 3/7（槽29） | 两组O1 |",
        "",
        "七项为：影响力联系人脉、非营利志愿服务、合作/倾听领导、教学评价、科研生产率、多样性实绩、数百万联邦拨款。这里比较的是一个明确候选人的诊断性事实子集，不是给整份答案打0分或3分，不要求所有七项都必须列出，也不以此编造岗位权重。原文、出现的准确短句、未出现的人工标签均保存在JSON。",
        "",
        "成员层面，005重复1的A2提问组（槽14）明确提出Roberts的合作领导记录，普通组（槽5）没有。重复2的A4提问组（槽28）把多样性写入主结论，普通组（槽37）只在missing的例外说明里承认该记录；后者不能被算成完全不知道。重复2提问组整合理由还从原件恢复了成员主结论未展开的合作信息，所以不能把理由覆盖差异全部归功于提问文本。",
        "",
        "## 为什么最终答案仍相同",
        "",
        "1. 009/012/023中，两种贡献已经传达足以改答的同一批局部事实。这里普通贡献本身有效，提问缺少额外需要解决的知识差异。",
        "2. 两组每个成员都引用自己的整个私有来源编号；宿主披露该编号对应的完整原文。005每份原文含多条人物信息，整合者即使没从成员结论得到某条事实，也能自行从原件读取。8个配对整合的原件逐字一致。保留完整原文有核验价值，不能为了制造方法差距而删原件；当前没有干预证明它就是持平的唯一原因。",
        "3. 005出现资料选择和比较上的共同缺口：8份提问首轮都围绕初答首选Stevens的筹款、创新或品行展开，没有把Roberts教学/科研或非营利机构拨款作为主要问题。提问仍围绕原稿的论证框架，未保证把自己独有的相关事实带入比较。这个模式与注意力受初稿影响的解释相符，尚未通过换初稿/无初稿条件隔离因果。",
        "4. Roberts为非营利机构争取数百万联邦拨款的事实，在A4原件中明确存在，也进入所有整合包；两组A4两遍的主结论及四份整合理由都未处理它。岗位要求successful fundraising，不能只反复争论其政治竞选筹款而忽略另一条直接相关记录。最终参考选择缺少数值权重，这仍不影响我们定位这个具体遗漏。",
        "5. 提问并未消除基础推理和范围问题。009重复2的A3两组（槽64/73）均写confirmed ICU capacity，公共资料只提供大型ICU和当班医生，不等于已确认可接收床位；最终整合结合A4的缺床信息改正。023两组A4均不同程度把蚊虫滋扰扩张为必须有室内/遮蔽容量，任务没有直接要求室内场地。不能把最终答对等同于所有中间步骤正确。",
        "",
        "## 全部32组配对记录",
        "",
        "下列判断按成员当时能看到的资料和其明确条件作出。成员暂荐的选项与全局参考不同不自动判错；更保守、不选总答案也不自动算更好。同一主要事实已交付不代表整段没有错误。",
        "",
        "| 任务/遍/成员 | 普通最终槽 | 提问最终槽 | 人工配对观察 |",
        "|---|---:|---:|---|",
    ]
    lines.extend(f"| {t}/{rep}/{m} | {o} | {q} | {note} |" for t,rep,m,o,q,cue,note in PAIRS)
    lines.extend([
        "",
        "## 对后续的建议",
        "",
        "把“成员先提一个问题”保留为候选表达方式；目前不要把它作为已经证明能提高团队正确率的核心贡献。005中两遍重复的理由覆盖改善是实际证据，也不能被最终持平抹掉。",
        "",
        "下一步设计应围绕一个更具体的能力要求：成员能从自己独有资料选择会影响任务判断的证据，整合者能将这条证据与当前解答中的具体判断比较并合理调整。005说明单纯提出关于旧稿的问题尚不能保证这个选择；009/012/023说明普通贡献已能完成直接约束的组合。先把这两个边界作为设计依据，再决定最小方法改动，避免因为单题遗漏添加完整表格、固定角色或多轮检查。",
        "",
        "证明相对普通协作的增益，可以继续使用同资料、同成员与匹配预算的普通贡献对照。全信息单Agent可作为诊断上限，不是继续研究这条主线或证明相对普通协作改善的先决条件。本轮未追加付费实验，也未改动原始输出、冻结评分或任务集合。",
    ])
    (RUN/"PAIRED_CONTRIBUTION_REVIEW.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(dict(reviewed_final_deliveries=64,member_pairs=32,identical_evidence_pairs=len(evidence_pairs),
                          roberts_focused_coverage=[dict(slot=c["slot"],coverage=c["focused_fact_coverage"]) for c in coverage],
                          new_model_requests=0),ensure_ascii=False))


if __name__=="__main__":
    main()

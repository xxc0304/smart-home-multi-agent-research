"""Offline summary of the named 20261025 runs, including the last run reviewed on 26th."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GROUPS=[
    ("可执行条件与程序报告",[
        "candidate-004-probe-live-20261025-r1","candidate-004-probe-live-20261025-r2",
        "candidate-transfer-probe-live-20261025-r1","candidate-screening-probe-live-20261025-r1"],
     "004：文本1/2、程序2/2；迁移：2/4、3/4；十题筛查：6/20、9/20",
     "有局部和多题正信号；条件形成/编码/采用仍不稳，部分收益不能归于正确执行。"),
    ("直接局部应用",["local-application-probe-live-20261025-r1"],
     "普通3/8、直接应用2/8；另6次完整原件单Agent诊断6/6",
     "没有方法收益；6/6同时改变了资料、旧稿及字段，不单归因于协调。"),
    ("资料与资源校准",[
        "local-judgment-moon-calibration-live-20261025-r1","local-judgment-moon-supplement-live-20261025-r1",
        "local-rule-resource-calibration-live-20261025-r1"],
     "月球14次中止后独立补充10次；规则校准12次",
     "部分私有知识确有价值，部分是模型已有常识；库存题有歧义，不作无争议成功。"),
    ("自主提问形成局部贡献",[
        "local-rule-frontend-live-20261025-r1","local-rule-confirmation-live-20261025-r1"],
     "开发6/18→9/18；宽口径8/18→9/18；新实例15/36→18/36",
     "是有效局部增补计数，不是团队准确率；有重复局部收益和反向损失。"),
    ("固定贡献的下游整合",["local-rule-adoption-live-20261025-r1"],
     "两组11/12；两份失分均为理由与choice不一致",
     "局部贡献差异未传为最终净收益；完整原文与整合可补偿成员差异。"),
    ("四任务真实协作贡献对照",["hb-local-contribution-live-20261025-r1"],
     "普通6/8、先提问6/8；8个配对选项相同",
     "分散事实可被组合改正公共初答；新首轮提示未增加最终成绩。"),
    ("先证据再对接共同稿",["evidence-first-live-20261025-r1"],
     "次级原始选择两组2/4、4个配对相同；冻结口径普通另有1个技术unknown",
     "第一遍找到并保留拨款，第二遍又漏；普通组也能补出并实际使用，没有稳定增量。"),
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records=[];groups=[]
    for name,names,outcome,meaning in GROUPS:
        selected=[]
        for dirname in names:
            p=ROOT/"runs"/dirname;state=read(p/"progress.json")
            requests=[json.loads(line) for line in (p/"requests.jsonl").read_text(encoding="utf-8").splitlines()]
            responses=[json.loads(line) for line in (p/"responses.jsonl").read_text(encoding="utf-8").splitlines()]
            assert len(requests)==len(responses)==state["attempts"]
            assert state["unknown_usage"] is False
            for field in ("input_tokens","output_tokens"):
                assert sum(x["response"]["usage"][field] for x in responses)==state[field]
            assert not any(x.get("retry",0) for x in requests)
            rec=dict(run=dirname,status=state["status"],requests=state["attempts"],
                     input_tokens=state["input_tokens"],output_tokens=state["output_tokens"],
                     request_log_entries=len(requests),response_log_entries=len(responses),retries=0,unknown_usage=False,
                     result_report=str((p/"RESULTS.md").relative_to(ROOT)),
                     progress_sha256=digest(p/"progress.json"))
            selected.append(rec);records.append(rec)
        groups.append(dict(stage=name,runs=names,requests=sum(r["requests"] for r in selected),
                           reported_outcome=outcome,interpretation=meaning))
    totals=dict(run_directories=len(records),requests=sum(r["requests"] for r in records),
                input_tokens=sum(r["input_tokens"] for r in records),output_tokens=sum(r["output_tokens"] for r in records))
    assert totals==dict(run_directories=13,requests=727,input_tokens=1254508,output_tokens=251521)
    data=dict(scope="The 13 explicitly named live run directories labelled 20261025; last batch reviewed on 2026-10-26. Not a complete calendar-day billing statement.",
              created="2026-10-26 Asia/Shanghai",new_api_requests_for_this_summary=0,
              totals=totals,groups=groups,runs=records,
              metric_warning="Do not aggregate local contribution scores, task reference agreement, calibration coverage and technical missingness into one accuracy.")
    research=ROOT/"research"
    (research/"DAILY_PROGRESS_INVENTORY_20261026.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    table="\n".join(f"| {g['stage']} | {g['requests']} | {g['reported_outcome']} | {g['interpretation']} |" for g in groups)
    inventory="\n".join(f"| {r['run']} | {r['requests']} | {r['status']} | {r['input_tokens']:,} | {r['output_tokens']:,} |" for r in records)
    report=f"""# 本轮连续工作的修改、实验与进展复盘

日期：2026-10-26。按10月25日批次标识、连同26日凌晨完成审核的最后一批整理；不因跨零点只保留最后72次。本文仅审阅现有记录，新增API请求0。

## 总判断

今天有真实的局部正信号，也有明确的持平/负面结果。问题分解、实验可追溯性和若干工程边界有所进展；没有完成“稳定增强多Agent知识互补与团队表现”的方法里程碑。诊断积累明显多于有效方法证据，实验数量不能等同于架构进步。

核对13个具名live目录的progress、requests和responses：共727次请求，输入1,254,508、输出251,521 tokens，包含中止及隔离请求，无记录到的重试、未知用量。未计本地回放/测试，也不将目录标识视为完整自然日账单。727不是任务数：其中大量是同题成员调用、重复、校准和下游整合。

## 修改与结果主线

| 工作 | 真实请求 | 已有结果 | 当前解释 |
|---|---:|---|---|
{table}

这些分母不同。6/18和15/36是同助手非盲标注的局部有效贡献，11/12和6/8是团队提交选项命中，校准则涉及特定知识覆盖；不能串成正确率涨跌曲线，也不能算一个全天总准确率。

随机权重/随机关注只讨论和审核过，没有在这些批次中测试；本轮没有RL或模型参数训练。

## 值得保留的正面进展

### 程序报告有具体可追踪的正面案例

十题筛查中程序9/20对文本6/20，四个配对收益、一个损害。023和027各一次收益与正确约束被应用的解释一致；另两次收益分别存在错误排除和无可执行条件，不能都算执行机制成功。程序组还得到更长报告，没有等长普通核对控制。因此保留正信号，不写成稳定15个百分点能力提高。

同时暴露条件覆盖不足（80份成员输出中55份conditions为空）、实体/状态编码错误、报告只留下正确选项却仍不采用。它们使这条路线尚不完备，却不让其正面案例失效。后面提问/时序候选持平，也不能回头抹掉这条线的局部收益。

### 自主提问有局部贡献形成信号

开发6/18对9/18，其中评分边界宽口径缩为8/18对9/18；新实例15/36对18/36，第一遍7对10、第二遍8对8。排程中同成员两遍得到正确并行条件结果，是应保留的重复局部收益；其他任务有反向损失，不是普遍改善。

固定贡献整合后两组均11/12，四任务普通与提问均6/8，说明该局部优势没有在已测条件形成最终净收益。不能将这两种层级的指标混为“先提升后下降”。

### 分散资料确实能进入解答

规则资料帮助换算/版本判断，月球专用接口资料提供无资料时无法确认的信息。后续医院、疏散、宴会题中，两组都将成员更新合起来改变公共初答；并非整个系统始终无法协作。

不过多数整合包已包含成员披露的完整原件，整合者可以独立重做。该事实不使实验无效，但限制“成员贡献文本带来独特收益”的解释。不能为制造差距删原件。

## 今天具体学到的失败机制

1. **有事实仍可能抽象/绑定错。** 车主不等于驾驶者，医院有大型ICU不等于当前有床位，未来修复时间不能压成当前是否ready，唯一道路关闭不能被一般的“一条道路”解释覆盖。程序执行只保证对表示计算，不保证表示忠实。
2. **事实已到场仍可能不进入比较。** 005拨款原件已经披露却多次漏用；022/023可承认负面更新又保留旧选项，对新选项反而要求更充分的保证。
3. **知道局部结论不等于完成应用。** 直接局部应用3/8对2/8，强制交付修订没有让模型稳定跨过从事实到判断更新这一步；一些成员仍把局部有效与证明整题必须改选混在一起。
4. **改变提问形式不足以自动改变知识选择。** 四任务提问组31/32首轮明确问句、普通0/32，行为改变确实发生，但最终选项仍相同。
5. **共同稿不是遗漏发生的必要条件。** 证据先行候选第一遍提取并保留拨款，第二遍无共同稿首轮仍漏；普通第二遍能自行补出并明确比较。因此不能继续把共同稿锚定当成唯一已知根因。
6. **正确推理可能未正确提交。** 归档整合的两份失分都在reasoning推导正确、choice填错。它是语义提交一致性问题，不是JSON损坏，也不能用正确理由替换实际提交得分。

这些是不同环节，需要不同证据。今天更准确的结论是缺口已更具体，尚未找到一个可靠解决它们的统一方法。

## 工程进展与仍需承担的问题

正面：从模型重复抄引文改为来源句柄和宿主呈现，减少纯机械抄写负担；补全精确名称/ID与来源权限检查；冻结任务、提示、代码、预算；真实完整响应回放与长负载检查；单条格式违约按依赖隔离，避免所有独立工作停掉；缺失评分保留unknown，所有结果与原文可追溯。

不足：004首次接口没有锁定候选名称/ID与额外null标记；月球因You/you逐字引用违约整批停；末端自报采纳字段反复漏。将末端自报字段升级为整份答案硬门槛是过度收紧，而非底层问题被修好。新最小末端接口只请求choice/reasoning，4项本地验证通过，尚未启用旧冻结批次。工程改善确实减少了损失，但今天仍未达到格式可靠性目标。

13批中两批stopped、一批completed_with_quarantine，其余按各自合同completed。最后72次全部发生、仅1条末端元数据隔离，选择和理由仍可作另列原始字段审阅；保持正式隔离和次级2/4对2/4核对分开，不因技术缺失制造方法优势。

## 今天进展如何评价

| 维度 | 评价 |
|---|---|
| 研究问题理解 | 有进展：能区分资料是否有用、表示是否忠实、是否正确应用、是否真正改解答及提交是否一致 |
| 局部方法证据 | 有但有限：程序报告、自主提问都有应保留的实例和小幅计数收益 |
| 团队最终效果 | 尚未达标：直接应用未受益，后续整合/四任务/证据先行均无稳定增量 |
| 架构收敛 | 尚不充分：多次在表示、交付、提问和可见时机间切换，缺少一个经验证的主机制 |
| 工程与复现 | 明显补强，但接口设计有重复的过严和漏审成本 |
| 投入产出 | 作为诊断获得了信息；对“稳定提升”这个主要目标，当前产出偏低，不应以修改/测试数量美化 |

今天应被记为一次范围较大的筛选和排障，而非有效架构已经建立。两道开发题小试的持平不证明所有独立形成知识方案无效，但没有证据继续直接扩本版本。仍相关于主线；其中大量调用集中在单成员贡献形成，尚未覆盖原来实际应用后提供者反馈的机制，不能将其全部称完整CoReTA测试。

## 建议如何收敛

保留所有正反证据，不把程序辅助净收益与自主提问局部收益合成架构胜利，也不一概判作“全白做”。普通贡献仍是有效基础；当前直接应用与证据先行实现暂不扩跑。

下一阶段先选定一个主攻环节及一个真正增加判断依据/可验证操作的机制。优先从程序报告真实起效的023/027案例，以及普通流程成功使用005拨款的路径中确定需要保留的能力。一个合理优先点是“已正确传达的局部证据如何实际约束比较/求解”，同时承认表示会错；不能直接强制遵守所有报告。

没有这样的具体机制之前，暂停继续按失败改一段提示再付费。无需追求所有问题一次解决，也不要求复杂训练或庞大架构；需要一到两个重复可见、成本可交代的真实改善。随机加权目前只有设想，不作为已有解决办法。

## 可核对的运行清单

| 目录 | 请求 | 终态 | 输入tokens | 输出tokens |
|---|---:|---|---:|---:|
{inventory}

对应原始报告均位于各目录RESULTS.md；跨批汇总数据与progress摘要hash见DAILY_PROGRESS_INVENTORY_20261026.json。所有过程判断沿用原报告的同助手事后非盲性质，没有新增独立人工标注。
"""
    (research/"DAILY_PROGRESS_REVIEW_20261026.md").write_text(report,encoding="utf-8")
    print(json.dumps(totals,ensure_ascii=False))


if __name__=="__main__":
    main()

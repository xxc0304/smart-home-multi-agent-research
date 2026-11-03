# 首批8条真实记录案例

整理日期：2026-10-29。详细原始请求、解析资料包和原始响应保存在[CASE_SEED_8.json](CASE_SEED_8.json)；原文件保持不变。本页的判断是助手定点核读，未完成人类独立标注。

目的性选择正反/边界案例以完善观察规范，**不是代表性抽样**：8个案例单位、7道基准题；共享初答的两个分支、同题重复、同题跨模型记录均不作为不同独立题。以下“对/错”先按冻结参考答案，语义忠实性另核。没有一条因此被认定为已校准的稳定能力专家。

| ID | 题/来源 | 可观察现象 | 最适合检查的环节 |
|---|---|---|---|
| C01 | 030，第1次，IMP适配 | 普通团队从正确多数转错误多数；资料路由分支保留正确结果 | 正确贡献的保留、后续修订 |
| C02 | 033，第1次，IMP适配 | 初答无参考选项，路由后全体选中参考答案 | 组合信息、生成新候选 |
| C03 | 007，第2次，IMP确认 | 普通终票2:2，路由4票正确；有成员明示追随另一成员 | 意见依赖、有效纠错与回退 |
| C04 | 008，第1次，IMP确认 | 只接收原始资料的分支也从对改错 | 完整信息下的推理/自我修订 |
| C05 | 004-age-10，局部重建 | 年龄限制已说出，接收者仍选不符年龄对象 | 约束理解、条件冲突、信息使用 |
| C06 | 023-road-89，局部重建 | 相同任务两条件终答不同，局部稿也并非固定 | 时效/预期判断、内容与历史依赖 |
| C07 | 019，作者GPT-4.1 | 道路阻断说法后出现开放说法，最终一致错误 | 冲突传播、取舍、最终整合 |
| C08 | 019，作者Gemini-2.5-Pro | 最后答对，但过程声称外部核验、发布记录无独立回执 | 正确结果与过程证据分开 |

## C01：030，正确多数在第二轮丢失

原始目录：[imp-adaptation-live-20261026-r1](../../runs/imp-adaptation-live-20261026-r1/progress.json)，repeat=1。shared初答slot1–3：A1未选，A2选Skylake/option_2，A3选Peak/option_1；参考为option_2。普通第一轮7–9形成2票正确，第二轮10–12变成2票Peak、1票Skylake，评分1→0。IMP的4–6和13–15均全票Skylake。

重点阅读：[普通A1第二轮010.raw.txt](../../runs/imp-adaptation-live-20261026-r1/010.raw.txt)、[IMP A1第二轮013.raw.txt](../../runs/imp-adaptation-live-20261026-r1/013.raw.txt)。普通A1引用A3关于A2私人资料未出现的说法；路由分支能直接讨论bank frozen/co-investor限制。

可确认：同共享初答下两协议有不同轨迹，正确候选存在后仍可丢失。待核：部分理由把12小时安排的条件适用范围扩大；该对照同时改变资料可见性和交互形式，不能单独证明去从众或某个组件有效，也不证明A2具有稳定专长。

## C02：033，协作价值不止保留原有正确答案

同目录repeat=1，shared slot17–19为Atlas/Gemini/Gemini，没有参考Nova/option_3。普通20–22及29–31最终仍选Gemini；IMP23–28两轮全选Nova，评分0对1；全信息单体32也选Nova。

重点：[023.raw.txt](../../runs/imp-adaptation-live-20261026-r1/023.raw.txt)、[024.raw.txt](../../runs/imp-adaptation-live-20261026-r1/024.raw.txt)及JSON内对应收件。原始信息包含通路限制、冷藏维护/备用电力、Nova恢复供电等条件。

可确认：有新的参考候选在组合资料后出现。因此只研究“让团队听原来答对的人”会漏掉一类协作收益。待核：部分回答将main highway解释成“唯一可行通路”，答对不自动证明每一推理忠实；分持条件下初答未选中参考，也不等于各成员已犯可独立避免的推理错误。

## C03：007，意见依赖有直接文本，终票却不是全错

原始目录：[imp-confirmation-live-20261026-r1](../../runs/imp-confirmation-live-20261026-r1/progress.json)，repeat=2。初答38–41：A2/A3选参考Starlight/option_2，A1/A4选Cape/option_3。普通第一轮A4改对，形成3:1；第二轮A2在slot55改为Cape，终票2:2。依该批tie评分为0.5；IMP终票50–53全对，评分1。

重点：[055.raw.txt](../../runs/imp-confirmation-live-20261026-r1/055.raw.txt)包含“I follow A1's stronger-supported reading”。这说明输出中存在意见依赖，不能仅凭该句就确定心理机制或反事实原因。

可确认：存在纠正后回退，团队不同成员反应不同。待核：需审查A1所述依据是否真的更有力，区分有效权衡、错误事实与不当追随；不把2:2叙述为错误多数，也不将两名初答正确者自动称为校准专家。

## C04：008，不能把这次改错直接归因于从众

同目录repeat=1。初答22–24：A3选参考Eddie/option_1，A1选Mickey、A2选Billy。IMP A2 slot29第一轮选Eddie，slot32第二轮改选Mickey；两个协议最终均参考评分0，全信息单体37也选Mickey。

已比较JSON中29/32的实际PACKET：**只有previous_answer改变，资料和其他字段相同；传入的是来源内容，没有其他成员的推荐答案。** 因此它是“没有同伴推荐也能回退”的边界案例，而非已经确认的从众证据。第二轮并非完全相同提示，因为自身上轮答案变了。

重点：[029.raw.txt](../../runs/imp-confirmation-live-20261026-r1/029.raw.txt)、[032.raw.txt](../../runs/imp-confirmation-live-20261026-r1/032.raw.txt)。需要进一步核“lied”“路线/时间”相关推断，排查任务歧义与答案依据；现有记录不能在推理不稳、先前答案影响、随机性之间定因。

## C05：004，明确说出限制仍未被正确应用

原始目录：[local-reconstruction-live-20261026-r1](../../runs/local-reconstruction-live-20261026-r1/progress.json)，case_id=004-age-10。局部slot1/3都说S02中guilty person<30；终答slot2/4均选父亲option_4，而参考为儿子option_3。局部文本及终答又加入driver/passenger、证词是否可信等判断。

重点：[003.raw.txt](../../runs/local-reconstruction-live-20261026-r1/003.raw.txt)、[004.raw.txt](../../runs/local-reconstruction-live-20261026-r1/004.raw.txt)与实际请求。接收者持S01，S02经局部报告传入，且有historical_work；不能把旧草稿当本轮独立初答。角色/驾驶判断是否有原始依据应逐项核验。

可确认：“信息被说出来”不等于最终约束被应用。尚不能确定责任全在接收者；分享稿可能混入了不受支持的角色解释，接收者也把来源可信度当作冲突处置。这正适合区分用户提出的“没分享好”“没理解/用上”与“自身推理错误”。

## C06：023，分支差异不能直接当单因素效应

同目录case_id=023-road-89。visible_draft局部25、终答26改为参考GrandOak/option_3；isolated_rebuild局部27、终答28仍Lakeview/option_1。S01说唯一通路因洪水关闭、expected to remain impassable through the weekend，任务为周六晚宴。

重点：[026.raw.txt](../../runs/local-reconstruction-live-20261026-r1/026.raw.txt)、[028.raw.txt](../../runs/local-reconstruction-live-20261026-r1/028.raw.txt)。两条件局部稿内容不完全一致；“预计持续关闭”也不等于每个时点已经确认关闭。

可确认：接收者对时间条件与不确定性的处理会影响最终选择。待核：是否过度要求现场确认、是否误用其他成员旧判断。不能单凭4个槽位宣布哪种重建策略稳定更优，也不能把差别全归于草稿可见性。

## C07：019，明确冲突之后未形成可靠整合

作者原文件：[hidden_generated_gpt-4.1.json](../expertise-literature-survey-20261028/hidden_generated_gpt-4.1.json)，conditions[0].runs[104]（索引从0计）。初答Person1 Blue River，其他三人Greenfield，**没有人初答参考Oakridge**。round2中出现South Street受阻说法，后续又有人称其开放，终票全Greenfield。

原始定位及选段见[旧019作者轨迹报告](../expertise-literature-survey-20261028/CASE_019_AUTHOR_TRACE_AND_LITERATURE.md)及本轮JSON的C07。不能把它写成“初始正确专家少数被压倒”。它更适于检查关键限制如何被公开、被冲突覆盖，以及是否被正确整合。缺少原始随机分配映射时，不从Person编号推断隐藏事实归属。

## C08：019，正确终答不等于可验证的正确过程

作者原文件：[hidden_generated_gemini-2.5-pro.json](../expertise-literature-survey-20261028/hidden_generated_gemini-2.5-pro.json)，conditions[0].runs[100]。初答Blue River/Greenfield/Blue River/Greenfield，终票全Oakridge，命中参考。对话与最终理由说EOC给出核验报告；发布run里未见独立工具调用/回执字段。

可确认：记录里存在“已核验”的语言，但当前文件不能为该外部核验提供独立证据。不能因为缺少回执就断言真实运行绝无外部操作，也不能将该案例计成“已验证成功核查”。它用于督促标注把最终正确、证据忠实、真实核查分开。

## 从案例到下一步

这批案例已经足以建立候选观察表：资料是否可见、贡献是否忠实、关键命题是否被回应、理由是否被正确应用、改答与终答如何变化；“没听”“从众”“不理解”等解释先不自动贴标签。先让人独立核验事实与定位，再决定要比较哪两种机制。没有据此报告机制频率、因果结论或论文主结果。

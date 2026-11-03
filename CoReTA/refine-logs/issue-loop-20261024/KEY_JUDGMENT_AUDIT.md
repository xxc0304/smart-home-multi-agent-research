# 关键判断复核：反馈之前，问题是否成立

复核者：本助手。读取现有原始请求、输出及作品记录，无新模型调用、无独立人工复核。选取005闭环前两项问题、005原流程终稿、004/034既有诊断及对照，不用于估计失败频率，也不把定性选项金标当成每一步推理的真值。

## 005：两项问题不能作为已发现的真实错误

原记录：runs/issue-loop-comparison-live-20261024-r2/hb-dev-005-r1/ground_issue_loop_v2/{state,requests,responses}.json[l]。

### R1.I1：合并引用O2/O3是否错误

O2引用A3的S03：`Has been observed drinking heavily in public, including at univer-sity events`。O3引用A4的S04：`Has been observed drinking heavily in public, including at university events`。W5说：`Peer reports O2 and O3 also record an observation of heavy public drinking at university events; I cannot verify that from my own originals`。

检查意见认为W5把两个来源混成一个来源、可能夸大独立佐证。原句确实没有分析两个底层报告是否独立，但它用了复数peer reports，引用了两个载体，也明确未核验；没有声称这是两个独立观察或已独立佐证。

**复核：可讨论的表述精度建议，现有证据不足以判为事实错误或已发生的来源混淆。** 更清楚说明来源依赖可能有用，但不能把未说明独立性自动等同于错误声称独立性。也不能从两份材料重复同一事实推出两份独立证据。

### R1.I2：open_points没重复unverified是否错误

W5对应open_point：`Stevens' fundraising credit is contested: the $15M Florida gift was primarily another's, and a peer report says he left the Mississippi deanship before raising building funds.` 正文还写`that should be verified`，末尾再次说明`those candidate facts are unverified and should be reference-checked`。

检查意见称open_point未重复unverified，因而把募资信息表述为确定事实。可是句子本身已有`a peer report says`，并非无归属的事实断言。

**复核：不支持将此计为确定错误；最多是独立阅读open_point时增加限定的编辑建议。** 不能通过要求每个位置重复同一免责声明制造问题。

### 编辑者接受意见意味着什么

缺失末尾右花括号的CHOOSE响应，在离线仅追加闭合符以供阅读后，两个disposition均为accept。但该响应未被运行器接受，也未进入后续修订；这是文本中的接受意图，不是有效选择/修订结果。

它提示一个风险：检查者先制造偏弱问题，编辑者再补出接受理由，可能形成彼此强化的非关键修订。因为只有一个中断窗口，这个解释仍是待检验假说，不能断言闭环普遍会诱发这种行为。

## 005：有效信息已进入，最终标准权衡未得到充分检验

原记录：同批ground_access_only_v2/state.json的W7及终稿检查。

W7承认Stevens募资证据减弱、抑制新想法、公共饮酒等报告，同时保留其行政领导和学术/技术经历作为选人主因；Roberts的多样性和联邦拨款也已加入。终稿仍为option_2，两个终稿检查均no_issue_found，原金标为option_1。

**可以确认：** 信息并非没有到达，也并非所有意见未被使用；权限说明在这条轨迹中被正确采用。选项没有转为金标，检查没有发现足以阻止该选择的问题。

**不能确认：** 仅凭金标差异不能证明某个权重必须如何设定。该题没有给定唯一数值权重，不能把“不选Roberts”本身编码成一个无需论证的事实错误。这里更合适的审查对象是：是否准确区分已报告事实与评价，是否同样对待各候选人的证据，是否说明关键反证为何不足以改变比较。

原贡献中也已有维持选择的建议：闭环O2写`Keep option_2 unless the concern is corroborated at a level that outweighs the academic-leadership fit`，O1称`This does not overturn option_2`。因此不能把未改选全部归因于编辑者忽略专家；提供者自身也可能已经接受原结论。

## 004：不是没用上知识，而是附加假设与联合约束处理失败

原记录：runs/selective-application-live-20261023-r1/requests.jsonl logical_call=1及对应输出；refine-logs/selective-application-20261023/SEMANTIC_AUDIT.json logical_call=1、2。

输入公共任务写Mr.X 53岁，儿子17岁；公开P-S02说肇事者小于30岁。CONTRIBUTION建议正确使用汽车约束排除摩托车Z，同时加入`The son was a passenger, so exclude him too and prosecute Mr. X`。原任务所给父子回家句子不确定谁是驾驶员，没有确立儿子是乘客。

输出将附加断言写为`the son is described as a passenger`，并选择53岁的父亲。它知道汽车排除Z，也写明under-30与父亲年龄冲突，却用饮酒故事及来源权重维持父亲结论。K条件输出把S01酒精及S03男性称为`two independent clue sets ... converge`，仍未满足年龄约束。

**复核：** 有效汽车信息已被采用，但错误乘客前提也被采用；输出没有满足已可见的联合条件。不能把“直接原件”与“间接报告”的身份区别作为自动丢弃一个相反约束的充分理由。该案例中车主/驾驶者酒精语义也有歧义，不能用额外编故事解决。

后续判断上下文诊断中，仅资料E也两次选错；加显式正确联合推理G两次选对。因此旧稿锚定或同伴影响不能独自解释004错误，而显式推理帮助可能有用。G由实验者直接提供关键推理，未证明成员会自主发现该帮助。

## 034：错误纠正覆盖了可见原文

原记录：runs/selective-application-live-20261023-r1/requests.jsonl logical_call=3及对应输出；同批SEMANTIC_AUDIT.json logical_call=3、4。

接收者SELF_MATERIALS.S01原句：`The latest radio advisory said the chemical cloud is drifting north, making Pine Retreat dangerous.`

K输出：`A2's correction is fair and I adopt it ... not something the advisory explicitly labels`；F输出：`A2 is right to correct my wording: S01 reports northward drift, not explicitly that Pine is dangerous`。

**复核：确定的来源内容误述。** 原件明确包含对Pine危险的报告。是否现实中确有危险、是否该报告可靠，与“报告有没有写这句话”是不同问题。最终Cedar选项仍正确，所以这是来源保真损害，不是该题选项准确率下降。

后续上下文诊断M两次均明确接受同类错误改述，E/B/G没有出现同样的明确否认。样本很小、条件间独立生成，支持一个局部风险线索，尚不足以认定唯一因果机制。

## 哪些解释需要修正

| 解释 | 本次判断 |
|---|---|
| 资料没到达，是主要失败原因 | 不能统一解释：034原件直接可见；004相关公开约束也可见。 |
| 意见没传到修订者，补闭环即可 | 不充分：005问题本身偏弱；034错误意见已经被采纳。 |
| Agent一概不会部分采用 | 不成立：原选择性应用实验的四个简单控制中，两种提示均能保留有效部分、拒绝错误部分。 |
| 有效意见都被编辑者忽略了 | 不成立：005内容已被加入，且提供者也建议维持option_2。 |
| 所有错误都是旧答案锚定 | 不充分：004仅资料条件同样失败。 |
| 格式失败说明闭环机制无效 | 不成立：闭环后续未完成；但技术可靠性代价真实存在。 |

## 更有依据的工作判断

至少有三类不同缺口：识别错误附加前提/保留原文内容；跨信息组合满足约束；判断检查意见是否真正成立并影响目标。005另有未由数值标准确定的证据权衡，不宜和前三类确定错误混算。

最近改动主要增加了可见性、权限清晰度和意见追踪，没有直接提供这三种判断的独立可靠依据。程序可保证“回应了”，无法由此保证“回应正确”。这解释了为什么流程执行得更完整，仍可能没有实质收益；不是对所有架构干预无效的证明。

## 下一步边界

暂停把问题账本继续扩为主架构增强。先用上述确定错误与正确对照，明确各子问题应如何被判定，以及验证究竟依赖原文对照、联合约束还是开放权衡。已有日志能完成错误分类，但不能比较尚未实施的解决方法；不要再把更长的检查提示或更多状态字段当作能力已经提高。

如果后续进入新方法验证，应针对一类明确缺口，在未用于设计的案例上检验有效纠正与误改；同时保留简单正确对照。004/034只作开发案例，005只作开放权衡案例；不直接重跑它们并把调试成功当泛化。此文未提出新的运行批次，API=0。

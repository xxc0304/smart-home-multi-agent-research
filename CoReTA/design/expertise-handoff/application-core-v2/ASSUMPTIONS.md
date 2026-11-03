# 实现前决定

ASK=never。依据用户已授权的独立v2最小重构，编码前记录；不是效果结论。

| ID | 未完全定死之处 | 本轮选择 | 类型 | 来源 |
|---|---|---|---|---|
| A01 | 新实现如何隔离 | 新增coreta.application_v2，继承现有Runner的贡献/路由/预算框架；v1不改 | interface | default |
| A02 | 清空missing的解释放哪里 | 使用本次application.result与binding.use，原回复C/拒绝理由一并保存；程序不认证解释充分性 | semantic | default |
| A03 | 暂定上游如何传播 | 允许有条件结果；绑定waiting/provisional上游时后继不能获得无未决的完成状态；仅显式依赖参与传播 | semantic | default |
| A04 | 老候选关联如何保留 | 更新target时将候选中该U映射到新版本；新应用自动关联当前候选；旧关联只能明确excluded或retire后去除。artifact=null也不抹旧关联 | semantic | default |
| A05 | 如何退役路径 | retire_applications与excluded分开；退役U使显式后继stale。excluded仅解除候选关联时保留U历史，不判原C错 | semantic | user |
| A06 | 格式恢复怎样避免部分提交 | 先在注册表副本检查整份更新、回复处理、候选关联，再一次提交；失败不改U/W或pending | interface | default |
| A07 | 请求如何绑定应用 | 明确指定一个U优先，否则选最近活动U或唯一待补U；修订时按A12映射。歧义时要求target_refs给出一个当前U。Q记录由程序补application_ref | interface | default |
| A08 | 评分与任务类型 | 首版沿用已有15物品ranking包、独立离线评分；不把U机制限制说成适用于所有任务 | semantic | default |
| A09 | 本轮验证范围 | 用户要求修改，本轮不新增/运行测试，不发API；可记录代码与入口已交付，不能宣称主干已运行通过 | semantic | default |
| A10 | 最终状态 | 模型unresolved与候选U的程序派生阻塞并列记录；存在任一阻塞不得reviewed_no_defect | semantic | user |
| A11 | artifact=null但应用依据改变 | 保留旧候选文本；若U或候选关联变化，产生新W版本，使旧核查不自动背书新依据 | semantic | default |
| A12 | 本次新/修订U伴随请求 | 明确指定的当前U优先；原target自动映射到新U；未指定U时默认最近活动U，不要求引用尚未分配的ID | interface | default |
| A13 | 候选依赖失效后的调度 | 最终核查前优先处理stale应用，按创建顺序先处理上游；要求更新、退役或排除焦点U。无进展且无请求时停止并保留未决，仍受原预算约束 | semantic | default |
| A14 | 后续离线验收 | 用户“开始下一步”承接离线验收计划；使用明确标注的脚本回复替身，真实Gateway/Runner/入口；禁止真实网络。测试输出不作为模型成功或能力提升证据 | semantic | user |
| A15 | 回复的退休与部分拒绝 | 明确退役原请求U本身即可处理该交接，C仍保留，不要求再判回复错误；若同一C既被使用又被部分排除，仍算接受，须更新原U或退役原路径，不能借excluded绕过目标检查 | semantic | sweep |
| A16 | W/Q/V引用与依赖传播 | 可见W/Q/V允许作为应用的对话上下文引用；状态传播只沿bindings中直接声明的U，不从C/W/Q/V内容推断间接U依赖。需要传播的应用依赖须直接列U | semantic | sweep |
| A17 | 核查意见的应用目标 | 核查明确指向唯一当前U且V被接受时，下一次APPLY须更新/退役该U；明确拒绝V可保留原U。仅指W或多个U时由模型定位，不强制任意选一个 | semantic | sweep |
| A18 | 单缺项上限范围 | 上限统计所有未退役/未被替换且missing非空的U；仅excluded解除候选关联不释放该名额，须解决或退役该路径 | semantic | sweep |
| A19 | 集成与长输入补验 | 从正常run入口经过真实调度构建依赖链；不同长度的脚本文本用于输入压力，不是模型输出样本或能力结果；检查单次脚本输出不超既有输出上限，超输入限应在传输前停止 | semantic | default |
| A20 | 内容核验记录 | 独立inspect入口导出Q/核查、原应用、后续APPLY、候选前后和原始引用；内容正确性及实际使用判断留空，供人工核验，不自动按状态转移打成功分，不读离线金标准或修改求解记录 | semantic | default |
| A21 | 最小真实schema检查 | 用户开始承接真实接口兼容检查；使用原DeepSeek传输与动态APPLY schema，3个固定JSON复制场景，最多3次HTTP、零自动重试/格式恢复，首失败停；不运行解题提示、不评分、不建立效果结论 | semantic | default |
| A22 | 新任务准备 | 首开发包复用官方学生会长4候选/4成员及全部16条私有事实和原加总规则；准备集中、分散、全信息、无信息四条件，不将资料归属直接认定模型能力优势。原生三人HiddenBench保留为后续候选 | semantic | default |
| A23 | 适配状态 | 本轮只构建并核对数据；当前15项专用输入/schema/渲染/评分/提示尚未适配4候选或选择题，不制作可直接开跑的假准备包，不改冻结v1 | interface | default |
| A24 | 四项排名适配 | 后续实现仅支持现有4或15项完整排名，不将选择题硬转排名；v2局部继承/派生输入与合约，独立渲染/评分及基线运行方法，冻结v1原文件不变；15项的schema和提示保持原样 | interface | default |
| A25 | 独立校准单成员 | v2入口允许independent指定member，保留原队伍定义但只调用指定成员；结果明确requested_members，评分按此计算预期成员，入口将单成员上限设为4尝试；四项校准提示不携带其他成员目录，15项为兼容保留原提示 | semantic | default |
| A26 | 交付失败与备用候选评分 | 缺失/格式错误排名沿用最大L1处罚，四项为8，并单列delivery_failure；普通讨论中断后保留的driver初答仍可离线评分，但标为中断/备用候选并保留协议错误，不称最终成功。CoReTA未请求独立完整答案时预期独立成员为空 | semantic | sweep |

继承只复用现有功能，不引入新的模型提供方或工具权限。语义判断、隐含依赖和未登记缺口仍可能错误。源标记user表示已接受规格中的决定；其他默认明确由本轮实现选择。

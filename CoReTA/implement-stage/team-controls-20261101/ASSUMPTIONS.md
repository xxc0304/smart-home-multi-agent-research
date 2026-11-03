# 编码前选择台账

ASK=never；用户已明确开始整体审核与离线实现，未启动真实实验。

| ID | 未定项 | 选择 | Class | Source |
|---|---|---|---|---|
| A01 | 对照/轮次 | 四分支、共享4初答；两工作轮每人一次，私有短终答；私人只见自身历史 | semantic | user |
| A02 | 提示文字 | 初答/终答用短答案指令；工作自然语言同一核心指令，区别只在可见历史/频道；不加核查清单/强制服从 | semantic | default |
| A03 | 披露 | C/D初答后用相同中性校准优势提示，E本人也接收；不提供当题正误 | semantic | user |
| A04 | 采样/长度 | B1 temperature .7/top_p .95/top_k 0，初终答64/work512；所有成员和分支对应阶段一致；新建中性GenerationConfig，只继承checkpoint的BOS/EOS，不继承隐藏采样/惩罚项，保存实际配置；明确不改B0 greedy | semantic | sweep |
| A05 | 随机配对 | 实际首遍固定seed20261102（运行器强制），题序/actor/阶段确定偏移；四分支对应请求相同seed，B/D发言顺序相同；不声称相同token随机轨迹 | semantic | sweep |
| A06 | 答案/投票 | 复用B0固定前缀去除及官方规范化，最高票答案类均匀抽签；初答seed+1000/终答seed+1001，四分支相同；不读gold | semantic | user |
| A07 | 主次指标 | 团队平票期望EM主、实际抽签EM/F1并报；固定专家个人EM和转移/读出损失单列；不是机制真值 | semantic | default |
| A08 | 技术失败 | 初答失败终止该题依赖；单分支工作/终答失败阻断该分支、其他分支可继续；不完整无完整主比较/无默重试 | semantic | default |
| A09 | 空输出 | 实际生成空短答案作弃权/错误计分；空工作作无贡献消息记录；非字符串或传输失败为技术失败，不混用 | semantic | default |
| A10 | 预算 | 每批有限walltime必填；加载/单token/保存有软截止开销，未EOS达上限/时间标OUTPUT_LIMIT并阻断依赖；OOM或模板/长度ValueError停批，修配置另存技术版本 | interface | default |
| A11 | 运行前提 | 真实运行只D前1/2/8/32；须已有同底座/adapter的真实C资格证据；本轮不生成C或自行封专家 | semantic | user |
| A12 | fixture | 手写或CPU tiny均显式fixture，永远无真实主结果资格；不下载预训练权重 | semantic | user |
| A13 | 成本与统计 | 1–2含于8/32，32首遍仅开发；按完整配对题/关联组10000次bootstrap，seed20261102，题加权；不完整不冒充全批 | semantic | user |
| A14 | 本地模型后端 | 复用B0 HF/PEFT同一个本地模型；B请求disable_adapter，E请求启用；每请求新上下文，无隐式聊天状态 | interface | default |
| A15 | 空字段配置 | 模型/精度/完整长度/预算等待实机填，reviewed_for_run=false拒真实运行；不假定4090 | interface | user |
| A16 | 累计批次 | 实际入口强制1或2起步→8→32（后两者须接续前阶段），用新目录接续已完整前缀，配置/题序/seed不变；wall_seconds可按新批调整；不完整题不自动重跑，不按答案选择接续 | interface | sweep |
| A17 | D输入与分组 | 按既有split manifest中D顺序固定前缀，逐行只解析前n输入/标签；关联组从全D的既有关系元数据计算；仅显式score时读相应D标签，不重做语义数据审核 | interface | sweep |
| A18 | 运行资格绑定 | 读取已有B/E C评分文件及adapter来源，重新计算既定C资格；模型/revision/精度/量化/template必须一致，C题集合与固定160一致（文件顺序不必等于元数据排序），B1解码按本阶段政策。B1长度上限因讨论历史单独实测，超长拒绝且不截断，不要求与独答C相等；不生成C，不读取其题文/标签文件 | interface | default |
| A19 | actor位置 | 本开发批固定专家slot M1，发言/初答展示顺序随机而不是专家slot轮换；不能据此证明跨身份位置泛化。后续必要扩展再做slot平衡 | semantic | sweep |
| A20 | 原文与清理 | 历史保存原始短初答，终答同样原文；仅投票规范化/评分各路径清理一次B0固定前缀，不连剥多个前缀 | semantic | sweep |
| A21 | 诊断汇总 | 逐actor报告EM/F1、正确保留/损害/纠错的条件计数分母，不把成员数当题数；读出损失实际/期望分报；主cluster CI外附题级敏感性CI | interface | sweep |
| A22 | 资源记录 | CUDA记录批内累计peak allocated/reserved，CPU记不适用；加载和请求耗时/真实token均保存，不用fixture推测设备吞吐 | interface | sweep |

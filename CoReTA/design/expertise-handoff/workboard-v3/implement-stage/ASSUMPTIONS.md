# 实现选择记录

ASK=never；EFFORT=balanced；assurance=draft。先记录再实现。

| ID | 未确定处 | 本次选择 | Class | Source |
|---|---|---|---|---|
| A01 | 第一版接哪些真实输入 | CLI沿用v2已校验的4/15项排名Packets；核心adapter可替换，文本adapter仅Python接口；不声称已覆盖代码/数学实验 | interface | default |
| A02 | 消息的实际JSON外形 | 分阶段object，试用/收尾使用action、candidate_id/work等明确字段及null占位；由schema与动作联合约束，版本编号由程序分配 | interface | default |
| A03 | 实现预算与恢复 | 默认N-1周期；网络尝试硬上限N+(N-1)(N+3)+4，格式/传输自动重试均0；每阶段输出上限为开发保护值，非已冻结实验预算 | interface | default |
| A04 | 开发token上限 | INITIAL/TRY/FINALIZE=4096，OBSERVE=2048，CHECK=3072，CHOOSE=512；沿用模型配置输入上限、本地tokenizer；不静默截断 | interface | default |
| A05 | 工具执行 | 当前排名任务没有运行工具；本次不新增执行器。支持读取由调用方显式传入、绑定版本的真实观察接口；模型文字不能登记为工具返回 | interface | default |
| A06 | 错误如何影响结果含义 | 初始化结构错误可记录后继续其他成员；其他协议/传输/上下文错误停止流程并交F，标记interrupted，不记正常完成；F为空才无交付 | semantic | default |
| A07 | 信息分享 | 仅初始资料分散、解题通信可共享的任务；公开offer所带摘录是模型提交内容，引用存在不代表摘录真实；不自动给别人原件 | semantic | default |
| A08 | 什么算完整 | adapter只检查交付形状；排名须覆盖全部候选，文本为非空交付；没有内容真值判断，未决/错误答案仍可能形状完整 | semantic | default |
| A09 | 基线与评分 | 本次只交付新方法入口，不声称现有旧基线已完成公平预算适配；不新增评分、不用新结果进入旧scorer | semantic | default |
| A10 | 默认支持人数 | 主入口要求N>=3，N=2退化条件暂不接CLI，避免把单人复核误称独立双检查；人数仍不写死为3 | interface | default |
| A11 | 检查输入与引用 | 公开offer以自身O编号被引用；私有S来源在公开摘录里显示来源声明，但其他成员只可引用O，不获得S原件可见权限 | interface | default |
| A12 | 验证范围 | 实现交付时仅源码审查；用户继续下一步后，授权工程验证。本轮运行离线检查及最多12项固定复制兼容场景；不跑能力实验 | interface | user |
| A13 | 继承哪些旧预算字段 | 只继承原request/task timeout；新模块不携带未使用的max_interventions/max_final_reviews等旧参数 | interface | default |
| A14 | logical seed含义 | 沿用传输层默认17作为日志标识，不传采样seed，也不承诺可重复采样 | semantic | default |
| A15 | 无实际改动的试用 | 允许reuse当前版本；当两候选相同记录selection_unchanged，不把它当新知识已有效应用 | semantic | default |
| A16 | 拒绝理由返回是否等于解决 | 成功向原提供者发送下一次观察后只标记reason_delivered_to_provider，不推断理解、纠正或缺项解决 | semantic | default |
| A17 | 多条摘录可引用同一来源 | support允许同一合法ref的多条摘录，不按ref个数限制条目；仅声明来源的unique列表可按refs容量限制；输出仍有token硬上限 | interface | default |
| A18 | 不同资料包的条件名称不同 | CLI要求显式--condition，不把moon的distributed_r0默认为学生会长包的distributed | interface | default |
| A19 | 收尾直接使用未入选贡献或间接采用初稿 | 复用非编辑原稿先找作者；否则按已公开O由新到旧匹配本次申报来源，再按已有W由新到旧匹配其非编辑作者；无来源才轮转选依据检查者，不限于先前TRY入选者 | semantic | sweep |
| A20 | 复用不可变旧稿时本次来源如何传递 | 本次declared_sources作为APPLICATION_SOURCE_REFS随两检查包发送；不篡改原Work的历史声明，来源仍只是本次模型申报 | semantic | sweep |
| A21 | 检查能否读取被引用的其他原生候选 | 检查包同样提供已有候选区原文，避免只看前后稿而读不到被引用的W；继续排除本轮另一检查和use_record成功声明 | interface | sweep |
| A22 | 收尾可复用哪些候选 | FINALIZE.reuse只枚举形状可交付的候选；TRY仍可复用局部稿，FINALIZE.new仍可提交不完整尽力稿并按规则回退/失败 | interface | sweep |
| A23 | 小规模配对如何共享初答 | 每资料分配×重复生成一套四成员真实INITIAL，验证同成员包哈希后分别加载；不重采、不按得分挑初稿；独立初答开销在配对层记录一次 | semantic | user |
| A24 | 普通讨论的实际机会 | 四成员六轮同步快照讨论（24调用），每人可完整重解/批评/分享；编辑者最后一次FINALIZE（1调用），无强制offer/use/check-back流程 | semantic | default |
| A25 | 配对资源边界 | 两法后续最多25 HTTP，传输/格式自动重试0，总输出预算61440token、单请求输入32768估算、时间1800秒；不强迫v3用满。讨论24×2304+最终6144=61440；v3阶段上限原值合计同为61440 | semantic | default |
| A26 | 试跑范围与结论 | 仅学生会长集中/分散×2重复×2方法，共8方法单元；编辑者两重复为A2/A3，均非集中资料持有者A1；共同初答的ALOC只离线分层，不判整体优越性 | semantic | user |
| A27 | 停批与模型用量 | 任一技术错误/不完整用量/格式异常停止整个试跑；不因答案错而重跑。正常all_pass或未用完预算不算错误；已开始和未开始单元分别记录 | semantic | default |
| A28 | 缓存和历史产物如何进入结果 | 载入初答保留正常Work编号和初始候选原文，标cache origin；result保留所选Work与真实后续调用，用配对层合并初答，不伪报全部成本是后续成本 | interface | default |
| A29 | 本次新增普通讨论消息格式 | DISCUSS复用INITIAL的Work原生输出形状，FINALIZE复用已有动作契约；基线不引入额外评分或正确性裁判 | interface | default |
| A30 | 普通讨论上下文重复 | 完整消息内容只在CANDIDATES里一次展开，移除逐行重复正文的locations；DISCUSSION、CURRENT_WORK、FALLBACK只存轮次/作者/Work索引，不另复制全文；不删任何公开原文、不模型摘要。当前基线仅四成员pilot | interface | sweep |
| A31 | 初答与缺失用量的报告 | 配对层单列初答usage和HTTP；完整usage要求input/output均非负整数。另报全部未知/不完整用量次数，旧uncertain_usage_attempts只作传输错误计数 | semantic | sweep |
| A32 | 基线收尾预算声明 | 普通讨论包明确reserved_closure_calls=1；CoReTA维持4。它们仍各25调用及61440输出上限 | interface | sweep |
| A33 | 部分初稿与全员初错如何区分 | 全员未提供正确完整答案与四份完整初答均错分别报告；有null/局部稿时不把它记成四份完整答案均错。该离线标签澄清不改变原始交付分数 | semantic | default |

| A34 | 成功动作是否允许解释理由 | TRY/FINALIZE的reuse/new允许reason为null或非空字符串，作为可选解释原样留在响应日志，不改变候选选择/实际使用记录/检查者分配；unable仍必须给reason且不能声称实际使用 | interface | default |
| A35 | 修复验收与旧批次关系 | 旧批次保持停止；回放原始失败响应与当前schema/动作校验，并用脚本验证两法完整提交路径；全部标为离线工程证据，不回填旧状态、不计新增能力结果。本轮不启动新能力批次 | semantic | default |

| A36 | 如何区分当前能直接引用的原件与同伴转述 | 输入SOURCE_ACCESS按当前成员TASK/SELF_MATERIALS列直接原件，按实际可见REFERENCE_INDEX列公开报告；从公开offer.support及Work历史declared_sources生成转述编号→公开载体索引，全部标为未核验的来源声明，不读取他人原件、不从自由文本猜来源 | interface | default |
| A37 | 转述编号是否自动修正/扩权 | 输出形状不变；declared_sources只能引用当前索引中的直接原件或公开载体，转述原件ID不因被提及获得访问权。不自动删/改引用、不把声明或摘录认定为真实支持；两法共用输入与提示规则 | semantic | default |
| A38 | 本次修复如何验收 | 原始r2失败响应应继续被拒；仅在明确标记的离线诊断副本中移除4个非直接原件ID（原响应已经引用O8），验证其余内容不变且合法；同时覆盖两法来源链、原持有人引用与未知来源拒绝。本轮不续旧批次、不运行新能力实验 | semantic | default |

| A39 | 来源表示控制的最小范围 | 固定r3集中r2普通讨论A3的调用7（首轮讨论后）与25（最终提交）输入；原表示/标记未采集各2次，平衡先后顺序，共8个独立一步续写，不当成完整团队结果，不重采或按得分挑输出 | semantic | default |
| A40 | 标记未采集具体改变什么 | 只给该转录候选加source_declaration_status=not_collected_in_INITIAL_or_DISCUSS及一条说明，保留原declared_sources=[]、全部事实/访问范围/提示/预算；不填造来源。该标记是待检验表示，不修改r3主运行器 | interface | default |
| A41 | 复用哪份历史两法皆错输入 | 采用2026-10-21 SBP derived_error受控fixture；按原作者将7条公开贡献的content/support/support_refs/conditions/needs原文分组装入4份Work，A1无排名、其他共享排名A>B>C>D；旧C编号不作为新引用，公开载体为W。原始逐项事实和两处错误小计保留，不传fixture错误标签，不读取评分决定输入 | semantic | default |
| A42 | 历史复测预算与解释 | 两次重复编辑A2/A3、平衡两法顺序；共享同一受控初稿，各25后续调用/61440输出上限，共4方法单元100请求。与8个来源探针合计最多108，首技术错误停整个诊断、不恢复。属已知失败输入的新版复测，不是旧方法精确复现、独立新题或全员自然初错证据 | semantic | default |

| A43 | 来源探针包装错误是否使已授权历史复测永久未执行 | 原联合批在第8次响应多出JSON前说明时按规则停止，探针不重跑、7份接受输出与1份中断分开。将预定但未启动的历史复测另立独立批次，只执行原4方法单元/100请求，内容/方法/预算/顺序不变，不续原批。归档原launcher字节；此调整改变原联合停批安排，须在报告显式说明 | semantic | default |

| A44 | HiddenBench当前实施范围 | 只准备既定开发ID1/4/34/50，保留原生4/3/3/3成员及私有包；不读取其余53评价题进入输入，不启动模型，Schedule本轮不实施 | semantic | user |
| A45 | 选择题产物与泄漏隔离 | artifact为固定option_N标识或null，单选完整合法才可交付；原选项文本保持，按题ID固定打乱并独立映射gold。模型仅见匿名题ID/统一title/原description/shared/本人hidden；源name/correct_answer/源路径/评估映射仅离线构建与评分使用 | interface | default |
| A46 | 3/4成员的公平机会 | CoReTA后续上限(N+1)^2，即16/25；普通讨论(N+2)同步轮×N人+最终，5/6轮。两法同后续调用及按CoReTA阶段上限求和的总输出额度40448/61440；普通DISCUSS2304，最终5888/6144。共享真实初稿，不称实际输入成本相同 | semantic | default |
| A47 | 未采集来源声明如何呈现 | Board.add的sources默认改为None表示未采集，仍保留兼容declared_sources=[]并增加source_declaration_status=not_collected；显式传空/非空sources均标collected。两法初稿/原生讨论同样受此规则，输入提示解释未采集不等于无依据；不伪造来源且不改变引用权限 | interface | default |
| A48 | 单体参照和准备不冒充运行 | 四题各2重复，16团队单元，另各8次全信息/仅共享单体参照；两者各独立一步INITIAL，以不同资料包投影提供输入。准备清单最大334HTTP（318团队含共享初答+16单体）；本轮仅可审阅准备和离线脚本，不产生真实能力结果 | semantic | default |

| A49 | 新开发批的编辑者/参照调度 | 按固定题序下标+重复号作为ordinal取模选择编辑者，重复1普通先、重复2CoReTA先；不按答案路由。每对完成后各单独调用全信息和仅共享INITIAL参照，使用A1及原生完整/空资料投影，明确独立求解无后续交流，不读取团队输出 | semantic | default |

## 说明

A06/A08：中断回退、形状可交付与正确性分开。新result不含accuracy、passed或verified等能力断言。

A09：公平对照与真实任务矩阵属于后续独立实验冻结，不把“新方法模块写好”当“可以直接开展对比实验”。

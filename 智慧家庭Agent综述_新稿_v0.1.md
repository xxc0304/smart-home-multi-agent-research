# 智慧家庭智能体系统研究综述：从家庭整体 Agent 到大语言模型驱动的任务执行与多智能体协同

> 本文围绕智慧家庭智能体的任务执行、环境接地与多智能体协同展开叙述性综述。正文采用顺序编码引用；文献矩阵编号仅用于源文件整理，生成的审阅稿中不呈现。

## 摘要

智慧家庭的核心问题并不只是连接更多传感器和家电，而是使系统能够理解用户目标，感知家庭状态，规划并执行设备或服务动作，并根据环境反馈持续修正行为。围绕这一问题，研究范式经历了从基于规则和经典智能体的家庭自动化、活动预测与健康监测，到面向异构设备的多智能体协同，再到近年来以大语言模型为核心的家庭任务执行与动态环境评测。不同阶段的论文在术语、系统结构和评价指标上差异较大，容易将“多设备”“多工具”误认为“多智能体”，也容易将静态 API 调用成功率等同于真实家庭中的长期任务成功。

本文以“家庭任务执行闭环”为统一主线，即“家庭状态与用户意图感知—任务理解与分解—设备或服务规划—智能体/工具协同—动作执行—环境反馈与异常恢复”，梳理智慧家庭智能体系统的发展脉络和关键问题。本文首先按照 Agent 的组织形式进行分类，再按照应用任务标注能源、照护、安全、个性化和活动识别等专题，避免将系统架构维度与应用场景维度混为一谈。文章重点讨论早期家庭 Agent、近期 LLM Agent、多 Agent 协同，以及仿真环境和动态评测，并从任务成功、动作正确性、状态一致性、延迟、冲突处理、故障恢复、个性化和 sim-to-real 等维度比较不同研究路线。综述表明，智慧家庭 Agent 仍面临状态语义异构、长期执行不稳定、协同协议不完善、个性化与自主权冲突、评测缺乏统一标准等问题。考虑到研究对象横跨经典 Agent、正式出版物和近期预印本，本文按证据等级组织结论，不将不同环境和不同任务定义下的成功率直接进行横向合并。

**关键词：** 智慧家庭；智能体；大语言模型；多智能体系统；任务执行；家庭自动化；动态评测

## 1 引言

智慧家庭研究早期主要关注设备互联、环境感知和自动化控制。随着家庭设备类型增加，系统需要处理的不再是单个开关命令，而是包含多个设备、多个步骤、时间约束、用户偏好和不确定环境状态的复杂任务。例如，“我准备睡觉了，请把卧室灯调暗、关闭客厅电视，并在明早七点打开窗帘”同时涉及用户意图理解、设备状态查询、动作顺序安排、定时触发和执行结果确认。如果家庭中还存在老人、儿童、访客或多个家庭成员，系统还必须考虑身份、权限、隐私和个性化差异。因此，智慧家庭的关键技术问题可以概括为：如何将用户目标、家庭状态、设备动作和环境反馈组织成可靠的任务执行闭环。

“Agent”并不是大语言模型出现以后才产生的概念。早期智慧家庭工作已经使用家庭整体 Agent、分层 Agent、移动 Agent、设备 Agent 和服务 Agent 来表示感知、预测、决策和控制过程。例如，MavHome 将家庭组织为能够感知环境、学习居民行为并选择自动化动作的 Agent 系统 [H20]；随后有研究进一步将活动预测、异常检测和照护者介入结合起来，用于居家健康监测 [H21]。这些工作虽然不具备今天 LLM Agent 的自然语言推理能力，但已经包含了家庭任务执行的若干基本环节。

近年来，大语言模型为家庭 Agent 带来了新的交互方式。SAGE 等工作让语言模型通过工具选择、设备 API、状态读取和执行反馈完成家庭任务 [H04]；HomeBench、SMH-Bench 和 PersonalHomeBench 则分别从有效/无效指令、多设备操作、环境接地推理、自动化、长期记忆和个性化等方面评测家庭 Agent [H01, H05, H06]。与此同时，家庭多 Agent 研究并没有消失，而是更多地集中在异构设备控制、边缘编排、能源调度、老年照护和资源约束等问题 [H17, H24, H25, H27]。这表明，近期家庭 Agent 研究存在两条互补路线：一条以单个 LLM Agent 的任务理解和工具执行为中心，另一条以多个角色或设备 Agent 的通信、分工、授权和协作为中心。

现有研究的一个困难是不同论文使用了相似但不完全相同的术语。“多设备指令”不等于“多 Agent 协同”，“多个工具模块”也不等于平级自治 Agent；反过来，一些早期论文虽然没有使用 LLM，却已经研究了今天仍然重要的状态感知、分布式控制、资源协调和执行反馈。若仅按“LLM Agent”或“Multi-Agent”检索和分类，就会遗漏重要的历史基础，也难以解释不同技术路线之间的连续性。

已有综述为本文提供了重要起点。Mekuria 等人的智能家庭推理系统综述通过六个数据库分析了 135 篇文献，系统总结了家庭自动化、辅助生活、符号推理和多住户冲突等问题 [H35]；其研究对象主要是 2019 年以前形成的智能家庭推理系统。本文不重复其对经典推理方法的全面编目，而是沿着“任务执行闭环”向前延伸，重点考察近年的 LLM Agent、工具接地、动态仿真、个性化、多 Agent 可靠协同和安全评测，并把这些新工作与早期 Agent 架构放到同一分析框架中比较。

基于此，本文的主要工作包括：

1. 以家庭任务执行闭环为统一分析框架，将早期经典 Agent、家庭自动化多 Agent 和近期 LLM Agent 放在同一演化脉络中讨论；
2. 根据 Agent 的组织层级和执行职责，将智慧家庭 Agent 系统划分为四类，并以应用任务标签补充能源、照护、安全和个性化等场景，明确区分多设备、多工具和多 Agent；
3. 从感知、任务理解、规划、协同、执行和反馈六个环节比较不同研究的能力边界；
4. 总结家庭仿真、数据生成和动态评测的发展，分析从静态动作正确性走向长期任务可靠性的必要性；
5. 归纳智慧家庭 Agent 在状态异构、长期记忆、多 Agent 协同、安全与评测方面仍待解决的问题。

## 2 文献检索与筛选方法

### 2.1 检索范围与来源

为避免把“Agent”仅理解为近期的大语言模型应用，本文采用跨时期、分层次的检索策略，覆盖经典家庭 Agent、家庭自动化多 Agent、家庭 IoT/智能环境以及 LLM Agent。检索时间范围为 2001 年至 2026 年 9 月，重点关注能够提供系统架构、任务定义、环境设置或评测结果的研究。

文献主要来自 IEEE Xplore、ACM Digital Library、Springer Nature Link、MDPI、Google Scholar 和 arXiv。Google Scholar 用于发现早期论文、引用链和不同版本；出版社页面用于核对作者、题名、会议或期刊、页码和 DOI；arXiv 用于补充近期预印本和作者公开版本；alphaXiv 仅用于快速发现近期论文和辅助阅读，不作为正式出版信息的唯一依据。

检索词按四组组合：场景词包括 `smart home`、`home automation`、`smart house`、`home IoT`、`intelligent environment` 和 `ambient intelligence`；Agent 词包括 `agent-based`、`intelligent agent`、`mobile agent`、`multi-agent system`、`cooperative agents` 和 `LLM agent`；任务词包括 `task planning`、`task execution`、`service composition`、`device coordination`、`activity prediction`、`failure recovery` 和 `execution monitoring`；评测词包括 `smart home simulator`、`benchmark`、`virtual home` 和 `environment-grounded`。此外，本文对核心论文进行作者、参考文献和被引工作的前向/后向追踪。

### 2.2 纳入与排除标准

满足以下条件的工作进入候选池：研究场景与家庭、家庭自动化、家庭 IoT、智能室内环境或独立生活直接相关；论文明确使用 Agent、agent-based、multi-agent、autonomous agent 或 LLM Agent 概念；并且至少涉及感知、预测、推理、规划、设备/服务作用、居民行为模拟或 Agent 间协作中的一项。正式期刊论文、会议论文、书籍章节和预印本均可纳入，但必须明确标注发表类型。

只讨论普通传感器硬件、通信协议或设备连接、没有自主决策机制的工作被排除。只将家庭作为背景、实际研究与家庭任务或家庭环境无关的通用多 Agent 论文被降为方法背景。能源、照护和安全论文可以保留，但单独标记其专题范围，不把专题结果直接推广为一般家庭 Agent 能力。同一工作存在预印本、会议版和期刊版时，保留正式版本作为主引，并记录版本关系。

### 2.3 文献矩阵与证据等级

每篇候选工作按照书目信息、场景、Agent 层级、任务、环境动态、方法、数据/仿真、评测指标、局限性和综述用途建立矩阵。Agent 层级至少区分家庭整体/分层 Agent、单 Agent、角色化多 Agent、设备/资源/用户 Agent 和 LLM Agent；评测字段则区分真实家庭、家庭实验室、仿真环境、快照测试和纯方法实验。

为避免不同来源的证据被混用，本文同时采用三级证据标记：一级为已阅读正式全文或开放全文，二级为出版社/会议官方页面、摘要和书目信息核验，三级为预印本摘要、引用链或可迁移方法背景。只有一级证据用于展开方法和实验细节；二级证据只支持页面或摘要能够直接确认的结论；三级证据仅用于发现线索或解释方法背景。预印本可以进入候选池，但不等同于已同行评审的正式发表结果。

最终工作矩阵包含 45 条记录，其中 31 篇文献被直接用于正文论述，其余 14 条作为历史补充、专题背景或方法背景保留，未参与主要结论的直接比较。正文主体同时覆盖正式出版物和近期预印本，并在参考文献中明确区分其出版类型。已有综述对经典智能家庭推理进行了系统整理；本文的重点则是将该基础与 LLM Agent、工具接地、动态执行、多 Agent 可靠协同和近期评测连接起来。本文采用分层叙述性综述方法，而非预注册系统综述；其结论以文献能够直接支持的系统机制、实验设置和评价结果为边界。

## 3 概念、范围与统一分析框架

### 3.1 智慧家庭 Agent 的工作定义

本文将智慧家庭 Agent 系统定义为：在家庭、家庭自动化、家庭物联网、智能室内环境或独立生活场景中，能够感知家庭状态，进行推理、预测或规划，与用户或其他 Agent 交互，并对设备、环境或家庭服务产生作用的自主软件或实体系统。

这个定义包含两个层次。第一，Agent 不一定由大语言模型驱动。规则系统、BDI Agent、移动 Agent、优化 Agent 和分布式设备 Agent，只要承担了自主感知、决策或行动功能，都属于本文讨论范围。第二，家庭 Agent 也不一定直接控制物理设备。活动预测、虚拟居民建模、家庭任务评测和照护辅助等工作，虽然作用链条可能经过中间控制层，但仍然研究了家庭环境中的 Agent 行为和任务执行。

本文重点关注以下问题：家庭状态如何被表示和更新，用户目标如何转化为可执行任务，设备或服务动作如何规划与协调，执行失败或环境变化如何被发现和处理，以及系统如何通过实验、仿真或基准测试证明其有效性。仅研究普通传感器硬件、通信协议或没有自主决策机制的设备互联工作，不作为本文主体。

### 3.2 Agent 组织形式与应用任务的二维分类

根据 Agent 在系统中的组织层级和职责，本文将相关工作划分为四类组织形式。应用能源、照护、安全和活动识别等专题则作为第二个维度单独标注。一个系统可以同时具有一种主要组织形式和一个或多个应用任务标签。

| 类型 | 主要特征 | 代表工作 | 典型问题 |
|---|---|---|---|
| 家庭整体/分层 Agent | 将家庭作为感知—预测—决策—控制整体，内部按层或接口组织 | MavHome、健康监测型家庭 Agent [H20, H21] | 居民行为预测、异常检测、自动化和辅助 |
| 单 Agent/工具接地 | 一个主要 Agent 负责理解请求、读取状态、调用工具并执行动作 | SAGE、HomeBench、SMH-Bench、PersonalHomeBench [H01, H04, H05, H06] | 自然语言理解、设备消歧、多步任务和个性化 |
| 角色化多 Agent | 感知、决策、执行、数据库、管理或边缘角色由不同 Agent 承担，并通过通信协议协作 | 移动 Agent、BDI 家庭系统、IAPhome、Magentix2、HearthNet、DCR [H17, H22, H24, H25, H34, H43] | 异构设备、通信、角色/规范、权限、冲突和故障恢复 |
| 设备/资源/用户 Agent | 设备、家庭、资源管理器或用户画像作为自治单元，围绕目标进行协调或优化 | 家庭能源、老年照护、可调自主性和多用户偏好冲突工作 [H23, H26, H27, H36] | 成本、舒适度、健康状态、资源约束、偏好冲突和人机介入 |

应用任务可以进一步标注为以下几类：

| 应用任务 | 研究对象 | 典型问题 | 本文中的作用 |
|---|---|---|---|
| 通用家庭控制 | 灯光、窗帘、家电和家庭服务 | 意图理解、设备消歧、多步执行 | 连接用户请求与设备动作 |
| 能源与资源调度 | 家电负载、储能、价格和舒适度 | 局部偏好与全局目标冲突 | 提供约束建模和分布式优化基础 |
| 照护与健康辅助 | 活动、异常、健康状态和照护者 | 风险识别、自主性调节和人工介入 | 强调安全边界与长期行为建模 |
| 安全与权限 | 家庭成员、设备权限和环境风险 | 身份、授权、提示注入和危险动作确认 | 约束 Agent 的可执行范围 |
| 个性化与多用户 | 家庭成员画像、记忆和空间偏好 | 偏好冲突、上下文变化和解释接受度 | 评价系统是否适应真实家庭关系 |
| 活动识别与状态推理 | 传感数据、活动序列和环境上下文 | 状态估计、可解释性和异常检测 | 支撑任务执行前后的环境接地 |

这个分类并不是按论文是否出现“Agent”一词进行机械划分，而是考察系统中是否存在独立的感知、决策、执行和协作责任。例如，HomeBench 中的“多设备指令”表示一条用户指令涉及多个设备，并不意味着存在多个自治 Agent；PersonalHomeBench 中的家庭记忆、视频理解和设备控制模块，也不自动构成平级多 Agent 系统。相反，IAPhome 的控制循环 Agent、数据引擎 Agent 和通信中间件之间具有明确的系统角色，因此可以作为角色化协同的代表。

H42 是本文保留的相关证据而非一种 Agent 组织形式：它研究活动识别结果如何被解释，以及解释如何影响用户对后续自动动作或照护提醒的理解和接受。将这类感知与信任工作单独标记，可以避免为了凑齐 Agent 分类而把所有家庭智能模块都称为 Agent。

### 3.3 家庭任务执行闭环

不同技术路线可以被映射到如下闭环：

> 家庭状态与用户意图感知 → 任务理解与分解 → 设备/服务规划 → Agent 或工具协同 → 动作执行 → 环境反馈、异常恢复与评测。

早期家庭 Agent 主要解决状态感知、行为预测和自动化控制；分布式多 Agent 工作重点解决角色分工、异构设备通信、资源协调和权限边界；近期 LLM Agent 则显著增强了自然语言任务理解、多步工具调用和个性化交互能力。三者的共同目标都是让家庭系统从“响应单个设备命令”逐步走向“完成带有目标、约束和反馈的家庭任务”。

该闭环也揭示了单次动作成功和完整任务成功之间的差别。一个 Agent 可能正确调用了某个灯光 API，却没有检查设备当前状态；也可能完成了第一步动作，却没有处理第二步的时间条件或执行失败。因此，家庭 Agent 的评价不能只看文本回答是否合理，还需要检查动作序列、最终状态、过程中的约束、无效请求拒绝和长期运行稳定性。

![图1 智慧家庭 Agent 的任务执行闭环](figures/figure1_task_loop.png)

图1将本文讨论的不同研究路线映射到同一个任务执行闭环。早期家庭 Agent 主要强化状态感知、行为预测和策略控制，LLM Agent 主要强化用户目标理解、任务分解和工具选择，多 Agent 研究主要强化角色分工、权限管理、资源冲突处理和故障恢复，动态 Benchmark 则开始检验环境反馈、时间推进和长期任务可靠性。该闭环说明，后续研究不应只比较“是否使用 LLM”或“是否包含多个 Agent”，而应进一步比较系统覆盖了哪些执行环节，以及是否能够根据环境反馈完成验证和恢复。

## 4 国内外研究现状及相关解决方案

### 4.1 国外研究现状

国外智慧家庭 Agent 研究大致经历了从家庭整体自动化、分布式多 Agent，到 LLM 驱动的开放任务执行和动态评测的演化过程。早期研究以家庭整体 Agent 为主要组织形式，重点处理环境感知、居民行为预测、异常检测和自动化控制。MavHome 将家庭视为能够感知环境、学习行为模式、预测下一活动并选择自动化动作的整体 Agent [H20]；健康监测型家庭 Agent 则进一步将活动预测、异常检测和照护者介入结合起来 [H21]。这一阶段解决的是“家庭能否根据环境和居民行为主动做出动作”，但任务表达主要依赖预先定义的规则、活动模型或结构化事件。

随后，研究重点转向异构设备、家庭服务和分布式控制。移动 Agent、BDI Agent、本体和服务组合等方法分别从通信、状态表示、设备能力建模和约束满足角度解决家庭自动化中的互操作问题 [H22, H24, H25, H37, H39, H40, H41]。能源调度、老年照护和多用户偏好冲突等专题研究，则将资源约束、风险等级、用户自主性和人工介入纳入系统决策 [H23, H26, H27, H36]。这类研究已经形成了较清晰的“感知—推理—规划—执行”结构，但通常需要预先配置设备、任务和规则，对开放式自然语言目标以及持续变化的家庭环境支持有限。

近年研究开始采用大语言模型处理自然语言目标和多步工具调用。SAGE 通过设备 API、状态读取和执行反馈实现工具接地 [H04]；Sasha、HomeBench、SMH-Bench 和 PersonalHomeBench 分别从创造性目标推理、有效/无效指令、多设备环境接地和个性化家庭任务等方面评测 LLM Agent [H01, H05, H06, H29]。SimuHome、HomeFlow 和 S5-HES 则把时间推进、环境状态、轨迹验证和数据生成纳入家庭 Agent 研究 [H02, H03, H33]。最新的边缘多 Agent 工作进一步关注共享状态、权限、租约、执行审计和重启恢复 [H17]。因此，国外研究的前沿重点已经从“能否生成合理动作”转向“能否在动态环境中持续、可验证且安全地完成任务”。

### 4.2 国内研究现状

从现有研究基础看，国内相关研究主要分布在智能家居控制平台、家庭物联网服务编排、传感器与执行器网络、边缘智能以及家庭健康辅助等方向。相关工作通常关注异构设备接入、家庭状态感知、控制循环组织和实时通信等工程问题。例如，移动 Agent 分布式控制架构将家庭控制划分为多个层次，并通过通信中间件和事件调度支持异构设备集成 [H22]；面向智能住宅的多 Agent 传感器与执行器网络则引入感知、决策、行动和数据库等角色，并使用 BDI、通信管理和 Petri 网分析约束协作过程 [H24]；IAPhome 等家庭控制平台进一步将设备组件、控制循环、数据引擎和中间件结合，用于真实家庭实验室中的灯光、窗帘和传感器协同控制 [H25]。

与国外研究相比，国内相关工作在设备接入、控制平台、通信效率和工程部署方面具有较好的基础，但直接围绕“开放式用户目标—大模型任务规划—多设备动态执行—失败恢复”形成完整研究链条的公开成果仍相对有限。现有研究更多以预配置场景、结构化控制逻辑或特定专题任务为对象，对自然语言歧义、设备状态过期、多个 Agent 的责任追踪、长期个性化和真实家庭安全边界的系统评测还不充分。需要说明的是，国内外研究并非完全割裂：许多国内工作使用国际会议或期刊发表，许多国外工作也采用通用家庭 IoT 和边缘计算技术。因此，本文按研究问题和解决方案组织比较，而不简单按照作者国籍或发表地区进行二分。

从相关论文的系统架构图可以进一步看出这一阶段的共同设计思想：家庭设备和传感器通常位于底层，通信中间件或数据引擎位于中间层，感知、决策和控制 Agent 位于上层，信息沿“环境状态上行—控制命令下行”的路径流动 [H22, H24, H25]。这种分层结构有利于隔离设备差异、复用控制逻辑并满足实时性要求，但也意味着高层决策依赖预先定义的接口和状态模型。与之相比，HearthNet 的架构图将共享状态、租约、权限验证和执行审计显式放入协同层 [H17]，说明近期研究正在把“多个 Agent 如何可靠地共同执行”从隐含的工程实现提升为需要单独验证的系统问题。

### 4.3 国内外相关解决方案归纳

现有研究可以归纳为六类相互衔接的解决方案。第一，针对家庭状态异构问题，研究者使用本体、知识表示、设备能力 Schema、共享状态和上下文模型描述传感器、设备和服务 [H24, H25, H37]；第二，针对用户目标和任务歧义，LLM Agent 通过自然语言理解、设备过滤、工具接地和状态读取将开放指令转换为可执行动作 [H01, H04, H29]；第三，针对任务依赖和资源竞争，经典约束规划、服务组合、分布式优化和多 Agent 协商用于安排动作顺序、能源目标和设备资源 [H23, H27, H39, H41]。

第四，针对动态环境和执行失败，动态仿真、状态复核、环境反馈、局部修复、补偿和重规划逐渐成为评测和系统设计的重要组成部分 [H02, H03, H05, H17]；第五，针对个性化与多用户冲突，研究引入用户画像、长期记忆、可调自主性和人工确认机制 [H06, H21, H26, H36]；第六，针对安全风险，相关工作开始关注权限控制、来源识别、风险路由和执行审计，但真实家庭中的长期安全验证仍然不足 [H17, H32]。

![图2 国内外智慧家庭 Agent 研究路线演化](figures/figure2_research_evolution.png)

图2从时间和问题演化两个维度概括了上述路线。可以看到，不同阶段并不是相互替代，而是逐层叠加：早期 Agent 提供状态感知和环境控制基础，分布式和多 Agent 方法提供设备协同与约束处理，LLM Agent 提供开放式任务理解，动态 Benchmark 和边缘编排则开始检验长期可靠性。当前研究的主要缺口并不在于缺少某一种单独算法，而在于这些能力尚未被稳定地组合到同一个可验证闭环中。

![图3 家庭 Agent 的关键问题与解决方案映射](figures/figure3_problem_solution.png)

图3进一步将“问题—方案—不足”对应起来。表格适合列出论文、指标和实验条件，图示则能够展示问题如何贯穿整个执行链条：状态异构会影响任务理解，任务歧义会影响规划，权限和资源冲突会影响协同，动态变化会影响执行和恢复，个性化会影响自主权与隐私，安全风险则贯穿动作提交和结果审计。因此，后续研究应同时报告语言任务成功率、最终家庭状态、冲突与失败类型、恢复代价以及安全和隐私指标。

### 4.4 本节小结

总体而言，国内外研究已经分别在家庭状态感知、设备控制、多 Agent 协同、LLM 工具接地和动态评测等方面形成了较完整的技术积累，但这些研究仍然具有明显的分散性。早期工作擅长结构化状态和确定性控制，却不擅长开放任务理解；LLM Agent 擅长自然语言和跨设备规划，却容易受到状态过期、设备幻觉和执行反馈不完整的影响；多 Agent 系统能够提供角色分工和权限隔离，却增加了通信、同步和责任追踪成本。由此，智慧家庭 Agent 的下一步重点应是将 LLM 的开放式理解能力、家庭状态与设备能力建模、多 Agent 协同协议以及确定性执行和恢复机制结合起来，并通过动态仿真与真实家庭实验进行统一验证。

## 5 早期家庭 Agent：从行为预测到分布式控制

### 5.1 家庭整体 Agent 与感知—预测—决策闭环

MavHome 是早期将 Agent 思想用于智慧家庭的重要代表工作。其基本目标不是让用户逐条控制家电，而是根据环境感知和居民日常行为，预测可能发生的活动并主动执行家庭自动化。由此，家庭被建模为一个能够观察环境、学习模式、预测下一事件并选择动作的整体 Agent [H20]。

这一思路说明，智慧家庭 Agent 的早期核心已经包含了三个后来反复出现的概念：第一，家庭状态需要由传感器和历史记录持续更新；第二，系统需要从日常行为中学习，而不是完全依赖手工规则；第三，Agent 的动作必须作用于环境，并由环境变化产生新的反馈。与近期 LLM Agent 相比，MavHome 的推理形式更加结构化，主要依赖行为预测和自动化策略，而不是开放域语言理解，但二者在任务闭环层面具有可比较性。

在健康监测方向，Das 和 Cook 将 agent-based smart home 用于居家健康辅助，形成了“传感器采集—活动模式学习—下一事件预测—异常检测—提醒或照护者介入”的闭环 [H21]。论文在 MavHome 基础上将系统划分为 Physical、Communication、Information 和 Decision 四层，并允许家庭区域或任务被组织为可重构的子系统。其方法包括使用显著活动片段挖掘规律行为，使用序列预测方法预测下一活动，并依据事件概率识别异常。

活动识别方向还暴露了家庭 Agent 中经常被忽略的可解释性问题。Das 等人的研究比较 LIME、SHAP 和 Anchors 等方法，并将识别依据转化为自然语言解释；这是因为活动识别结果可能进一步触发开灯、关闭设备、调节温度或照护提醒 [H42]。该研究报告 SHAP 生成合理解释的成功率为 92%，且在 83% 的抽样场景中用户更偏好自然语言解释而不是单一活动标签。H42 的研究对象是活动识别解释模块，不是 LLM Agent 或平级多 Agent 系统；它在本文中的作用是说明“状态判断是否可理解、用户是否接受解释”也应成为家庭 Agent 评测的一部分。

这类工作对今天的家庭 Agent 研究仍有两点启示。其一，家庭智能的价值不只体现在设备控制，还体现在对长期生活过程的建模，例如活动规律、健康趋势和异常事件。其二，家庭 Agent 的输出必须连接到具体的辅助动作和人机介入机制，而不是停留在预测一个标签。另一方面，早期实验主要基于合成数据、实验室数据和有限参与者，系统评价重点也在预测准确率和异常识别，不应将其直接解释为已经解决了真实家庭中的长期自主运行问题。

### 5.2 移动 Agent、角色化 Agent 与家庭自动化基础设施

随着家庭设备和服务逐渐异构，研究重点从单一家庭控制器扩展到多个功能模块之间的通信和协作。移动 Agent 研究曾尝试使用 CORBA 等分布式对象机制，将家庭控制组织为分层架构，并通过优先级队列处理实时事件 [H22]。这类工作关注的是服务迁移、异构系统互操作和实时事件分发，体现了家庭环境对低延迟和可部署性的要求。

BDI 和多 Agent 方法进一步将感知、决策、行动以及数据库等职责分配给不同角色。相关家庭自动化系统使用 BDI 模型表达 Agent 的信念、愿望和意图，并结合有限状态机、Petri 网或调节策略处理照明等结构化控制任务 [H24]。这类系统的优点是角色边界和状态转移相对明确，便于验证可达性、响应时间和通信吞吐；局限是任务通常被预先结构化，用户自然语言、开放式意图和长期个性化行为尚未成为主要研究对象。

IAPhome 则代表了更偏工程部署的路线。该系统通过通信中间件连接异构设备，将控制循环、数据引擎和配置管理等功能组织为多个 Agent 或组件，并在真实家庭实验室中验证灯光、窗帘和传感器场景 [H25]。其结果说明，多 Agent 家庭系统的难点不仅是“让多个 Agent 互相发送消息”，还包括设备能力描述、数据更新周期、控制程序配置、场景触发和人机反馈。换言之，家庭多 Agent 协同必须建立在可靠的设备抽象和状态同步基础上。

在显式多 Agent 之外，2016—2018 年的一条服务配置研究路线也为后来的工具接地和任务规划提供了中间层证据。加权约束满足方法把设备能力、服务依赖、用户偏好和优化目标统一到配置问题中，用于求解家庭自动化中的可行服务组合 [H39]。规则型服务定制工作则进一步把环境和用户上下文引入服务选择，并分析规则匹配的执行代价 [H40]。面向 IoT 智慧家庭的自动服务组合研究继续关注服务连接、语义描述和运行时重配置 [H41]。这些工作不应被标为 LLM Agent 或平级多 Agent，但它们说明“自然语言请求—设备能力—可执行服务组合”并不是近期才出现的问题；近期 LLM Agent 的新意主要在于用语言模型处理更开放的意图表达、任务分解和工具调用，而底层的能力约束、服务依赖与重配置问题仍然存在。

2017 年的 E-care@home 从上下文推理角度补充了这一基础。系统将异构传感器数据写入共享数据库，用模块化 SmartHome ontology 表示对象、时间、空间、事件和设备能力，再用增量 Answer Set Programming 推断活动和异常 [H37]。它还讨论根据信息目标自动选择传感器和执行器的配置规划。虽然 H37 不是平级多 Agent 系统，但它揭示了家庭 Agent 在执行前必须解决的状态语义、时间更新和能力互操作问题。

H34 将协同问题从设备层扩展到多住户组织层。该工作使用 Magentix2 和 virtual organization，以角色和规范约束不同 profile 的内部/外部 Agent 行动，说明家庭多 Agent 还需要回答“谁在什么身份下可以做什么”。基于公开出版信息可以确认其角色与规范机制，因此本文将其用于说明多住户组织问题，而不把场景示例扩展为定量实验结论。

多 Agent 也可以位于家庭感知和状态推理层，而不只负责设备控制。Jarraya 等人提出 DCR 分布式模型，以 Agent 范式组织智慧家庭的人类活动识别，并采用学习 Agent 和 distributed collaborative reasoning 支持在线识别 [H43]。这条路线提示：家庭多 Agent 的分工对象还可以是传感数据、局部状态和活动推理过程。本文将 H43 限定为“分布式感知/推理”证据，不把其公开摘要之外的模型细节、数据集或定量结果外推到其他系统。

### 5.3 专题应用中的多 Agent 协同：能源、照护与自主性调节

除一般家庭自动化外，多 Agent 还被用于家庭能源和老年照护等具有明确约束的专题。家庭能源管理通常需要同时考虑设备运行时间、电价、舒适度、峰值负载和全局需求响应，因此可以把不同设备或家庭建模为自治决策单元，再通过协商或分布式优化寻找局部偏好与全局目标之间的平衡 [H23, H27]。这类工作为理解资源冲突、分布式约束和局部—全局权衡提供了重要基础，但其结论主要适用于能源调度，不能直接推广到所有家庭任务。

老年智慧家庭研究则更关注系统自主性与人的介入之间的平衡。可调自主性多 Agent 系统尝试根据健康状况、时间、用户行为和人机互动情况调整自动化程度 [H26]。这提示家庭 Agent 的“更自主”并不总是更好：在照护、健康和安全场景中，系统需要判断何时自动执行、何时请求确认、何时把决策交给家人或专业人员。该问题后来也延伸到 LLM Agent 的权限控制、危险动作确认和长期个性化记忆。

H36 进一步把冲突来源从健康状态和自主性扩展到多个用户、空间和时间之间的偏好差异。该工作提出面向智能环境的多 Agent 偏好管理与冲突处理架构，并将用户在不同空间和时间之间的移动纳入适应过程 [H36]。这与 H29 的自然语言反馈、H31 的长期偏好适应形成互补：个性化并不只是“记住一个用户喜欢什么”，还要处理当前空间、同时在场成员和不同目标之间的动态冲突。H36 的当前证据主要来自官方摘要，因此这里只用于提出问题，不比较其具体算法收益。

总体来看，早期家庭 Agent 研究已经覆盖了感知、预测、任务分层、分布式通信、设备协作和人机介入等关键问题，但其任务通常较为结构化，系统输入和输出也大多由预定义协议表示。近期 LLM Agent 的主要变化，不是首次提出“家庭 Agent”，而是将自然语言意图、开放式任务分解和大规模知识推理引入既有的家庭执行闭环。

## 6 单 Agent 与 LLM Agent：从工具接地到家庭任务评测

### 6.1 工具接地与可执行任务

近期家庭 LLM Agent 的核心问题，是如何把语言模型生成的计划转化为真实可执行的设备操作。SAGE 将顶层 Agent 与多个分层 agent-tools 结合起来：Agent 接收用户请求后，根据动态提示树选择工具，读取工具返回的设备或环境信息，再决定下一步动作或终止执行 [H04]。设备交互工具还可以进一步处理设备消歧、属性读取、命令执行和 API 文档检索。

与只生成一段文本相比，这种架构强调了“工具接地”。Agent 的输出不再只是解释或建议，而必须对应设备接口允许的动作，并根据执行结果继续推进任务。对于持久命令或条件触发任务，系统还需要保存用户意图、写入条件检查逻辑，并在后续状态满足时重新执行。这些机制使家庭 Agent 更接近一个状态相关的程序执行器，而不是普通问答模型。

不过，工具接地并不等于任务可靠。首先，语言模型可能选择错误设备、误解设备能力或忽略当前状态；其次，多步任务中前一步动作可能改变后一步的可行性；再次，API 返回成功不一定代表物理环境已经达到预期状态。因此，家庭 Agent 需要同时具备状态查询、动作验证、错误恢复和必要时的用户澄清能力。

### 6.2 有效指令、无效指令与多设备任务

HomeBench 从有效和无效家庭指令出发，区分了有效单设备、无效单设备、有效多设备、无效多设备以及混合多设备等任务类型 [H01]。这一设计揭示了家庭 Agent 评测中的一个重要问题：系统不仅要完成正确的请求，还必须拒绝设备不存在、参数不合法、条件不满足或动作组合不可行的请求。

HomeBench 以虚拟家庭和 API 操作序列为基础，分别使用整条指令成功率和操作级 F1 等指标进行评价。整条指令成功率能够反映多步任务是否完整完成，操作级指标则可以区分“部分动作正确”和“整体任务成功”。这种区分对于家庭场景尤其重要，因为一个错误的附加动作可能导致整个任务的安全性或用户体验下降。

需要特别注意的是，HomeBench 中“多设备”描述的是任务涉及的设备数量，而不是 Agent 数量。一个单 Agent 可以通过工具调用完成多设备任务；同样，多个设备也不必然对应多个自治 Agent。因此，多设备任务复杂度和多 Agent 协同复杂度应当作为两个相互关联但不能混同的维度。

### 6.3 从静态 API 到动态家庭环境

静态工具调用测试难以覆盖家庭环境中的时间变化、用户干预和连续状态转移。SimuHome 将家庭任务放入具有时间和环境变化的仿真环境中，考察状态查询、隐式意图、显式控制和工作流调度等不同任务类型，并同时设置可行和不可行请求 [H02]。这类工作把评测重点从“模型是否生成了正确命令”推进到“Agent 是否能够在变化中的家庭环境中维持正确的任务状态”。

SMH-Bench 进一步将家庭 Agent 任务扩展到环境接地推理、设备控制、问答、歧义澄清、自动化和记忆等类别 [H05]。这说明家庭任务不只是把一句话翻译成 API 调用，还可能要求 Agent 查询家庭状态、理解用户历史、处理不完整信息、生成时间触发规则，并在多个回合中保持一致的环境模型。

动态环境带来的关键变化是：任务成功必须同时满足目标、过程和状态三个条件。目标条件要求最终家庭状态符合用户意图；过程条件要求动作顺序、权限和时间约束得到满足；状态条件要求 Agent 对设备和环境的内部表示没有明显过期或错误。只报告最终文本或某一个动作的准确率，无法完整描述这三类能力。

### 6.4 个性化、记忆与主动计划

PersonalHomeBench 将家庭 Agent 的能力扩展到个性化问答、反事实推理、家电功能推荐和主动计划等任务 [H06]。其关注点不再只是“如何控制一盏灯”，而是“在特定家庭成员、家庭布局、设备历史和用户偏好下，什么行动是合适且可执行的”。这使长期记忆、成员身份、情境信息和多模态观察成为家庭 Agent 的重要组成部分。

个性化同时带来新的风险。记忆越丰富，Agent 越可能利用家庭成员的隐私信息；自主计划越积极，系统越可能在用户未明确授权时采取行动。因此，个性化家庭 Agent 需要把“知道什么”“能够做什么”和“是否应该现在做”区分开来，并在高风险动作、涉及他人或无法确认意图时请求用户确认。

### 6.5 从目标导向执行到本地轻量化

Sasha 进一步展示了单 Agent 家庭系统如何处理欠明确的目标导向请求 [H29]。与“打开厨房灯”这类直接命令不同，“让房间舒适”需要 Agent 判断目标是否可实现、筛选相关设备、生成具体设置或触发—动作规则，并允许用户通过自然语言反馈进行修正。其 Clarifying—Filtering—Planning—Execution—Feedback 五阶段流程区分了一次性 immediate goal 与持续性的 persistent goal；全文实验表明，显式澄清和设备过滤能够在论文设置下减少错误设备选择与 false positive，但小规模用户研究中达到目标平均仍需要约 3 次命令。该工作的重要价值在于把传统家庭自动化中的固定规则与 LLM 的开放式目标解释连接起来，同时暴露了设备幻觉、错误设备选择、当前状态敏感性不足和计划相关性不足等失败模式。

IoTGPT 将研究重点从一次性计划生成推进到子任务分解和任务记忆复用 [H30]。系统先把复杂指令拆解为设备相关子任务，再将任务级、子任务级和上下文级信息存入分层 DAG 记忆，并在虚拟家庭中校验命令、根据环境属性抽象用户偏好，使后续相似请求可以减少重复的 LLM 调用。其 26 个设备、97 个任务的预印本实验报告了最高约 83.51% 的冷启动成功率，热启动相对提升最高约 18.31%，且延迟和成本进一步下降；这些数字受其固定 ground truth、虚拟环境和模型设置约束，不能与其他论文的成功率直接横向比较。该路线说明，家庭 Agent 的长期效率不一定依赖更大的模型，也可以通过可复用的任务结构和偏好抽象降低推理成本。不过，任务记忆本身也需要版本管理、错误修正、偏好冲突处理和隐私控制，否则一次错误的自动化可能被持续复用。

AdaHome 则从本地小模型部署角度处理效率和隐私问题 [H31]。它根据请求属于直接、间接还是模糊意图，选择不同复杂度的规划路径，并用 Chain-of-Draft 控制小模型的推理开销，再通过用户确认和修正更新本地偏好记忆。全文实验在统一 Llama 3.2-3B、12 个设备和 90 条指令上进行，direct、indirect 和 ambiguous 的成功率分别为 86.7%、86.7% 和 88.9%；纵向合成序列中的偏好一致性、临时偏差恢复率和偏好变化适应成功率分别为 87.5%、80% 和 100%。这些结果仍属于论文自身固定 schema、二值设备状态和预印本设置，不能直接与不同家庭环境中的 benchmark 成功率横向比较。

这三类工作共同表明，近期家庭 Agent 的研究重点正在从“能否调用设备 API”转向“能否稳定解释目标、复用经验、适应用户并在本地高效运行”。它们仍以单 Agent 或模块化系统为主，尚不能替代多 Agent 在权限、设备域隔离和冲突恢复方面的作用，但为未来的分层组合架构提供了任务理解、记忆和部署侧能力。

总体而言，单 Agent/LLM Agent 路线拓展了家庭任务的表达能力和交互灵活性，但当前研究仍主要集中在受控仿真、有限任务集和较小规模家庭状态中。它解决了“如何用自然语言描述任务”的一部分问题，却没有完全解决长期环境建模、设备能力异构、异常恢复、权限治理和真实家庭部署问题。这也构成了后续多 Agent 协同和动态评测章节的连接点。

## 7 多 Agent 协同：从角色分工到可靠执行

### 7.1 为什么需要显式的多 Agent 协同

单 Agent 加工具的架构能够覆盖许多家庭任务，但当系统同时面对异构设备、多个权限域、并发事件和边缘部署时，仅增加工具数量并不能自动解决协调问题。一个工具可能属于家庭服务器，另一个工具只能在手机端调用；一个设备动作可能改变另一个设备的可用状态；用户的即时请求还可能与定时自动化或其他家庭成员的请求发生冲突。在这些情况下，系统需要明确回答：谁负责提出动作，谁有权执行，谁维护共享状态，谁裁决冲突，以及失败后由谁恢复。

早期多 Agent 工作已经对这些职责进行拆分。H24 将家庭控制划分为感知、决策/管理、行动和数据库 Agent，使用 BDI 表示个体状态，再通过服务请求、状态报告和资源策略实现群体协作。该系统还使用有限状态机描述单个 Agent 的行为，以 Petri 网检查任务可达性和潜在冲突。H25 的 IAPhome 则把设备、控制回路、数据引擎和用户交互组件连接到统一的通信中间件，通过任务分解、资源调度、设备驱动和人机反馈完成结构化场景控制。H34 补充了多住户环境中的角色与规范，H36 则补充了用户偏好冲突和空间迁移；两者共同说明家庭协同不仅是设备间消息传递，还涉及主体身份、授权规则和多用户目标。

这两类工作说明，多 Agent 的新增价值不在于“把一个大提示拆成几段”，而在于引入可检查的职责边界和协作协议。相应地，多 Agent 系统也会产生单 Agent 不明显的新问题，包括消息延迟、共享状态不一致、重复执行、权限越界、局部目标冲突和故障后的责任追踪。

### 7.2 边缘编排中的状态、权限与冲突

HearthNet 是近期家庭边缘多 Agent 编排的代表性工作 [H17]。它部署了 Root Agent、多个领域 Manager Agent 和 Librarian Agent：Root Agent 接收用户请求、分解任务、仲裁冲突并签发执行授权；Manager Agent 负责各自设备域；Librarian Agent 记录协调流、任务状态和恢复事件；设备本身通过确定性适配器连接，不被直接当作 Agent。

该架构的关键不是 Agent 数量，而是把共享状态和执行权限外化为可检查的系统机制。Agent 通过 MQTT 通信，Git 仓库保存版本化家庭状态和审计时间线。一个改变设备状态的请求必须携带 Root Agent 签发的短期 actuation lease，并绑定设备范围、允许动作、参数范围、批准时的状态版本和过期时间。适配器在执行前检查 lease 是否存在、是否过期、是否超出权限，以及请求所依据的状态版本是否仍然新鲜。

HearthNet 将家庭任务组织为 Ground、Propose、Verify and Grant、Execute and Record 四个阶段。Agent 先读取当前设备状态、策略和版本信息，再提出领域动作；Root Agent 检查意图、权限、状态新鲜度和冲突规则后签发 lease；设备执行结果和审计信息最终写回共享状态。这样的设计把“提示词中要求 Agent 遵守规则”转换为“系统边界拒绝不满足条件的命令”，更适合涉及真实物理动作的家庭环境。

论文在一个小型真实 testbed 上展示了模糊意图协同执行、用户请求与定时例程冲突解决，以及 Agent 重启后的过期命令拒绝。实验报告了 4 个 Agent、约 10 个设备、3 类场景；其中模糊意图场景完成率为 4/5，冲突处理和过期命令拒绝在演示测试中达到 5/5。由于系统规模小、没有单 Agent 对照，也没有恶意 Agent 或大规模家庭实验，这些结果应理解为协议可行性证据，而不是多 Agent 普遍优于单 Agent 的性能证明。

### 7.3 专题任务的约束与可迁移性

能源管理是多 Agent 协同中最容易形式化的家庭专题之一。H23 和 H27 将设备、家庭或资源单元表示为自治 Agent，通过分布式约束优化、协商或需求响应机制，在成本、舒适度、峰值负载和局部偏好之间进行权衡。H27 进一步将家庭自动化设备调度建模为分布式优化问题，并在仿真和小型物理实验中考察峰值、成本和收敛行为。这些研究证明了多 Agent 在资源分配和局部—全局协调中的方法价值，但不应将能源调度结果直接外推为一般家庭任务执行能力。

老年照护场景提出了另一类协同问题：系统不只要决定“做什么”，还要决定“由谁做”和“自动做到什么程度”。H26 的 AAMA-IoT 关注根据健康状态、年龄、时间和用户行为调整系统自主性，并在模拟家庭中管理多类物体和设备。H21 的早期健康监测工作也将异常检测、提醒和照护者介入连接起来。它们共同表明，家庭 Agent 的协同对象不仅包括设备和软件模块，也包括居民、家属和照护人员。

因此，专题应用中的多 Agent 系统，其可迁移经验主要体现在约束建模、资源分配、风险分级和人机介入，而不是某个具体领域的设备控制算法。面向一般家庭任务的系统仍需要进一步研究：如何把能源、照护、安全和日常自动化的约束统一表示；如何在多个目标冲突时解释取舍；以及如何将用户确认纳入多 Agent 的执行协议。

### 7.4 单 Agent 与多 Agent 的互补关系

从当前文献看，单 Agent 和多 Agent 并不是简单的替代关系。单 Agent/LLM Agent 更擅长处理开放式自然语言、模糊意图、知识检索和跨任务规划；多 Agent 系统更适合处理设备域隔离、异构协议、权限边界、并发冲突和边缘自治。一个可行的家庭系统可能采用分层组合：由一个高层 Agent 与用户交互并生成任务目标，由多个领域 Agent 负责能力接地，再由确定性控制器、权限策略和设备适配器限制实际动作。

这种组合也带来新的接口要求。高层 Agent 不应直接假设所有设备都具有相同能力；领域 Agent 需要提供可验证的能力描述、状态版本和执行结果；确定性适配器需要拒绝越权、过期或格式错误的动作；评测还需要区分高层规划错误、领域工具错误、设备执行错误和环境反馈错误。未来的家庭多 Agent 研究，应更多比较不同分工方式在成功率、延迟、可解释性、资源成本和故障恢复方面的实际收益，而不是只报告 Agent 数量和通信拓扑。

## 8 动态仿真、数据飞轮与评测

### 8.1 家庭仿真从行为生成走向任务有效性

真实家庭数据存在隐私、采集成本、设备异构和长期标注困难，因此家庭 Agent 研究长期依赖仿真和合成数据。OpenSHS 是较早的开放家庭仿真基础设施之一：它将交互式活动采集与模型式事件复制结合，通过 design、simulation 和 aggregation 三阶段生成可扩展数据 [H38]。不过，OpenSHS 的多居民支持仍不完整，且 SUS 主要评价工具可用性，不等于数据真实性或任务执行能力。H28 在 Unity 3D 虚拟家庭中使用带调度器的 BDI 居民 Agent 生成日常活动和传感器数据，并通过 Orange4Home 数据复现、Classifier Two-Sample Test（C2ST）、活动识别和下一活动预测评估数据质量 [H28]。

H28 的结果体现了仿真评测中的一个重要原则：数据分布与真实数据不完全一致，并不必然意味着仿真没有用。论文报告模拟数据可以被 C2ST 完全区分，但只用模拟数据训练的模型在真实数据上仍取得约 80.10% 的活动识别准确率和 82.35% 的下一活动预测准确率。这说明合成数据的价值应结合下游任务有效性判断，而不能只看统计分布是否难以区分。同时，单一家庭、单一居民和有限活动范围也限制了结果的外推性。

### 8.2 从静态指令到动态工作流

家庭 Agent benchmark 正沿着任务复杂度逐步扩展。HomeBench 主要考察有效/无效的单设备和多设备指令，并同时报告完整指令成功率与操作级 F1 [H01]。SimuHome 将设备状态、时间推进、连续环境变化和工作流调度加入家庭仿真，覆盖状态查询、隐式意图、显式控制和可行/不可行请求 [H02]。SMH-Bench 则进一步加入环境接地推理、歧义澄清、自动化、多轮交互、记忆和复杂家庭状态 [H05]。PersonalHomeBench 将评测扩展到家庭成员画像、长期记忆、多模态事件、家电推荐和主动计划 [H06]。

这些工作可以形成一条由浅入深的评测演化链：

| 评测阶段 | 主要问题 | 代表工作 | 仍未覆盖的因素 |
|---|---|---|---|
| 设备动作正确性 | 指令是否转化为正确 API 动作，错误请求是否被拒绝 | HomeBench | 连续环境动力学、长期记忆和真实物理反馈 |
| 环境接地与时序执行 | 状态变化、时间约束和工作流能否被正确处理 | SimuHome、SMH-Bench | 大规模真实家庭、多用户长期运行 |
| 个性化与主动服务 | Agent 能否利用成员、偏好、事件和记忆生成合适计划 | PersonalHomeBench | 真实设备提交、风险动作和长期用户反馈 |
| 可验证训练与数据闭环 | 能否生成有效轨迹并用环境反馈训练 Agent | HomeFlow [H03] | sim-to-real、开放协议和训练成本 |
| 边缘真实执行 | 多 Agent 能否在异构设备上安全协调和恢复 | HearthNet [H17] | 更大规模、更多故障和跨家庭复现 |

HomeFlow 进一步将家庭仿真用于 Agent 训练，而不只是测试。其 HomeEnv、HomeMaker、Blueprint 和 MCTS-Flow 组成数据生成与验证流程，通过轨迹检查、逐步奖励和策略优化生成可用于训练的家庭任务数据。论文报告 SmartHome-Bench 包含 1,678 个测试实例，HomeFlow-RL 模型在其设置下取得较高成功率。由于该工作是近期预印本，且仿真环境和实验设置仍有待更广泛复现，相关数字应作为论文报告结果引用，不能直接视为真实家庭部署性能。

S5-HES Agent 从仿真平台建设角度补充了这一方向 [H33]。该框架由 Orchestrator 协调家庭构建、设备管理、威胁注入和优化等专门 Agent，通过 RAG、验证流水线和可替换 LLM 让研究者用自然语言配置家庭环境、设备行为和安全场景。全文报告了 118 类设备、22 类威胁、20,306 个知识文档块以及 Studio 到 Mansion 的 7—97 台设备扩展，并用检索质量、威胁生命周期和设备消息相似度进行评估。它的价值不在于证明某个家庭 Agent 已经能够长期控制真实设备，而在于尝试把家庭仿真从“需要专门程序配置的固定环境”变成可扩展、可标注和可复现的研究基础设施；但单种子、有限真实设备交集、单次生成规模和外部效度限制仍然存在。

### 8.3 家庭 Agent 的多维评价指标

现有论文的指标口径差异较大。为了比较不同系统，本文建议至少从以下维度记录结果：

| 评价维度 | 需要回答的问题 | 典型指标或证据 |
|---|---|---|
| 任务目标 | 用户要求是否最终完成 | episode/task success、完整指令成功率 |
| 动作正确性 | 每一步设备动作、工具名和参数是否正确 | 操作级 F1、参数准确率、计划 validity |
| 状态一致性 | Agent 认知的家庭状态是否与环境一致 | 状态差异、版本检查、最终设备状态 |
| 过程约束 | 顺序、时间、权限和资源限制是否满足 | 工作流成功率、约束违反次数、无效请求拒绝 |
| 可靠性 | 遇到错误、过期状态或 Agent 崩溃能否恢复 | 恢复成功率、重规划成功率、重复动作率 |
| 协同质量 | 多 Agent 是否减少冲突并保持责任可追踪 | 冲突检测、授权拒绝、消息开销、审计完整性 |
| 交互与个性化 | 系统是否理解用户偏好并在合适时请求确认 | 个性化准确率、计划偏好、用户确认率 |
| 可解释性与信任 | 用户能否理解状态判断及其触发动作，并愿意接受系统解释 | 解释合理性、自然语言解释偏好、解释后的接受度 |
| 效率与部署 | 系统是否满足家庭场景的延迟和资源限制 | 端到端延迟、P95/P99、计算/通信/能耗成本 |
| 泛化能力 | 仿真或一个家庭中的能力能否迁移 | sim-to-real、跨布局、跨设备品牌、跨用户 |

其中，任务成功和动作正确性必须同时报告。一个计划可能在语言上很合理，但工具名称或参数错误；一个动作序列可能局部正确，但最终没有达到用户目标。PersonalHomeBench 对计划偏好和计划可执行性的区分，HearthNet 对冲突拒绝、lease 验证和恢复事件的记录，都说明家庭 Agent 评测需要从单一准确率转向结果、过程和安全边界的联合评价。

### 8.4 当前评测的共同局限

第一，家庭环境仍然以仿真、快照或小型 testbed 为主。仿真便于控制变量和生成大量任务，却可能简化设备故障、用户临时干预和真实空间约束；真实 testbed 能展示端到端链路，但规模和可复现性有限。第二，不同论文的“成功”定义不一致，有的检查 API 序列，有的检查最终状态，有的依赖 LLM-as-a-Judge，有的只展示少量场景，直接横向比较需要谨慎。

第三，许多 benchmark 评估的是一个 Agent 的任务执行，而多 Agent 工作常用的是演示性场景，缺少单 Agent 基线、不同拓扑的消融实验和统计显著性。第四，数据和代码开放程度、设备协议、模型版本和提示词配置仍不统一。未来评测应公开环境状态、任务生成规则、设备能力 schema、工具调用日志、失败分类和随机种子，使不同 Agent 能在相同家庭环境中进行可复现比较。

### 8.5 跨阶段综合比较

将上述工作放在同一框架下，可以看到智慧家庭 Agent 的研究重点并不是简单地从“没有 Agent”发展到“有很多 Agent”，而是沿着任务闭环逐步增加能力和约束：

| 演化阶段 | 代表工作 | Agent 组织形式 | 主要解决的问题 | 环境与评测 | 主要边界 |
|---|---|---|---|---|---|
| 家庭整体与分层 Agent | H20、H21 | 家庭整体/分层 Agent | 行为预测、异常检测、健康辅助 | 传感器数据、实验室或合成数据；预测和异常指标 | 任务和设备状态较结构化，长期真实部署有限 |
| 活动感知与分布式推理 | H42、H43 | 可解释识别模块、学习 Agent 与分布式协同推理 | 活动识别、状态解释、在线感知协作 | 家庭传感数据和在线识别；解释合理性、用户偏好或摘要级方法证据 | H42 不是 LLM Agent；H43 的公开信息主要为摘要级证据，尚无可比的任务执行结果 |
| 角色化家庭自动化 | H22、H24、H25 | 移动、感知、决策、行动和数据库 Agent | 异构设备、通信、角色分工、QoS 和资源约束 | 家庭实验室、JADE/中间件、照明和场景控制 | 自然语言任务、开放意图和长期记忆较少 |
| 设备/资源/用户 Agent | H23、H26、H27 | 设备/家庭/资源自治单元 | 能源调度、可调自主性、局部—全局优化 | 仿真、物理实验或老年家庭模型 | 结论集中于能源或照护，难以直接推广 |
| 单 Agent/LLM 工具接地 | H04、H01 | 顶层 LLM Agent 加工具和 API | 意图理解、设备消歧、多步命令和无效请求 | 快照设备、虚拟家庭、任务 benchmark | 连续环境动力学、跨设备互操作和故障恢复仍有限 |
| 单 Agent/LLM 的目标、记忆与本地部署 | H29、H30、H31 | 单 Agent 加模块化规划、任务记忆或本地小模型 | 欠明确目标、子任务复用、偏好适应和效率 | 用户研究、任务 benchmark、本地模型对比 | 设备规模、跨家庭泛化和长期安全仍有限 |
| 动态家庭评测与训练 | H02、H03、H05、H06、H28、H33 | 单 Agent、虚拟居民、训练飞轮或仿真编排 | 时间推进、环境反馈、个性化、记忆和可验证轨迹 | 家庭仿真、合成家庭状态、真实数据迁移 | sim-to-real、用户干预和长期运行仍未充分验证 |
| 家庭 Agent 安全与多模态仲裁 | H32 | 单 MLLM、传统检测器和多 Agent mediation | 环境提示注入、授权判断、过度执行与过度拒绝 | 19 个 pilot 场景；UER/SCR；oracle 上界 | 没有实现路由器，样本规模和真实长期验证有限 |
| 边缘多 Agent 可靠执行 | H17 | 持久化角色 Agent 加确定性适配器 | 共享状态、授权、冲突、审计和重启恢复 | 小规模真实边缘 testbed | 规模、恶意故障和跨家庭复现不足 |

这张表显示了三条贯穿全文的连续性。第一，早期工作中的家庭状态、设备能力和行为预测，仍是今天 LLM Agent 进行工具接地和环境反馈的基础。第二，LLM 提升了任务表达和规划的开放性，但没有消除异构设备、权限和状态一致性问题，反而要求更明确的接口和验证机制。第三，多 Agent 的价值主要体现在分工、隔离、并发和恢复，而不是单纯提高语言推理能力。因此，未来系统更可能是“语言模型负责开放式任务理解，领域 Agent 负责能力接地，确定性协议负责授权和执行”的组合，而不是单一范式取代其他范式。

## 9 开放问题与未来方向

### 9.1 统一 Agent 层级与任务定义

当前文献中“Agent”可能指家庭整体控制器、BDI 软件实体、设备服务模块、虚拟居民、LLM 工具调用器或多个 LLM 角色。若不说明 Agent 是否拥有独立目标、状态、决策循环、通信接口和执行权限，就无法准确比较单 Agent 与多 Agent。后续研究应在论文中明确给出 Agent 的身份、状态、目标、工具、权限和协作关系，并区分多设备、多工具、多模块和多 Agent。

任务定义也需要从孤立命令扩展到完整 episode。一个家庭任务至少应描述初始家庭状态、用户目标、可用设备和能力、时间约束、环境扰动、允许的用户确认以及终止条件。只有这样，任务成功才具有可重复解释的含义。

### 9.2 家庭状态表示与设备能力互操作

H22 和 H25 所面对的异构设备问题，在 LLM Agent 时代并没有消失，而是从通信协议差异进一步表现为能力 schema、属性命名、状态语义和反馈粒度的不一致。不同厂商可能用不同方式表达“关闭”“待机”“锁定”或“温度达到目标”，LLM 即使能生成语法正确的调用，也可能误解其物理含义。

未来需要建立可验证的家庭状态和设备能力表示：一方面，能力描述应包含动作前置条件、参数范围、风险等级和预期反馈；另一方面，状态应带有时间戳、来源、版本和置信度。高层 Agent 可以使用自然语言规划，但动作提交前必须经过能力检查、状态检查和权限检查。这样能够把语言推理的灵活性与设备执行的确定性结合起来。

### 9.3 动态环境中的长期执行与恢复

家庭任务通常具有长时间跨度，执行过程中可能出现设备离线、用户改变意图、传感器噪声、定时器触发或外部环境变化。SAGE 已经展示了持久命令和错误返回，SimuHome 和 SMH-Bench 将时间与工作流加入评测，HearthNet 则进一步处理状态版本、lease 和 Agent 重启，但这些能力尚未在统一环境中被系统比较。

后续研究需要把执行监测和恢复作为一等任务，而不是失败后的附加功能。Agent 应能够识别任务处于未开始、执行中、部分完成、阻塞或已失效等状态，并根据当前环境重新规划；对于不可逆或高风险动作，还应在执行前获得更强的确认。评价时也应报告恢复时间、重复动作、错误扩散和最终安全状态，而不是只看初次成功率。

### 9.4 多 Agent 的可靠协同与安全边界

多 Agent 能够带来领域分工和并行执行，但也会增加通信、状态同步和责任追踪的复杂度。未来的关键问题包括：如何避免两个 Agent 同时修改同一设备，如何处理用户请求与自动化规则冲突，如何在某个 Agent 崩溃后安全接管，如何阻止越权或过期命令，以及如何证明协同协议在不同故障模式下仍然满足安全性质。

HearthNet 的共享状态、lease 和审计时间线提供了一个有价值的设计方向，但当前仍局限于小规模、诚实但可能崩溃的 Agent。更完整的研究应加入重放、伪造消息、恶意或错误建议、网络分区和设备适配器异常，并通过形式化约束、策略执行器或可验证动作接口限制 LLM 的影响范围。对于普通家庭部署，还需要考察本地模型、边缘计算和云端服务之间的隐私与延迟权衡。

PromptShield Home 从另一个角度说明了家庭 Agent 的安全难点 [H32]：系统不仅要判断动作是否符合设备 schema，还要判断输入内容是否真正来自有权发出指令的用户。该工作在 19 个 pilot 场景中比较传统检测器、单 MLLM 和多 Agent mediation，并分别报告 unsafe-execution rate、safe-completion rate、false-block rate 和 human-confirmation rate，以避免“全部拒绝”在类别不平衡数据上获得虚假的高准确率。结果显示传统检测器倾向于过度执行，MLLM 配置倾向于过度拒绝；不同层的正确案例具有互补性，但 94.1% 的 oracle 结果只是上界，并没有实现真正的路由器。因此，未来多 Agent 安全协同的关键不只是增加专家角色，而是建立可验证的来源识别、授权和风险路由机制。

### 9.5 个性化、自主性与人机共同决策

家庭 Agent 越了解成员偏好和生活规律，越可能提供主动帮助；但长期记忆也会增加隐私泄露、错误推断和过度自动化的风险。H21 和 H26 已经涉及健康监测、照护者介入和可调自主性，PersonalHomeBench 则显示个性化信息检索和主动计划会显著增加工具协调难度。

未来系统应把自主性视为可调节变量，而不是固定属性。对于低风险、可逆动作，Agent 可以根据用户习惯自动执行；对于涉及安全、健康、隐私或他人的动作，系统应提高确认等级，并解释使用了哪些状态、记忆和策略。用户还应能够查看、修改和撤销长期记忆，了解自动化规则的来源，并在需要时接管任务。

### 9.6 面向真实家庭的统一评测与可复现性

智慧家庭 Agent 最终需要在跨布局、跨品牌、跨用户和跨时间条件下运行，但当前研究往往只覆盖单一仿真器、少量设备或一个家庭 testbed。未来可以建立分层评测体系：先在可复现仿真器中测试任务与状态转移，再在包含真实设备的实验室中测试协议和延迟，最后通过隐私保护的长期试验评估用户接受度、误触发和维护成本。

统一评测还应同时报告能力和代价。除了成功率和准确率，还应记录 token/API 成本、端到端延迟、边缘资源占用、通信量、能耗、人工确认频率、隐私暴露面和失败后的恢复成本。只有将这些指标放在同一框架中，才能判断一个更复杂的多 Agent 或多模态系统是否真正适合家庭部署。

## 10 结论

智慧家庭 Agent 的研究并非始于大语言模型。早期工作已经围绕家庭感知、居民行为预测、健康监测、异构设备互操作和分布式控制建立了家庭任务执行的基本闭环；多 Agent 研究进一步引入了角色分工、资源协调、通信协议和人机介入。近期 LLM Agent 则将自然语言意图、工具调用、个性化记忆和主动计划带入这一闭环，并推动研究从静态设备控制走向动态家庭环境评测。

本文以家庭任务执行闭环为主线，区分了家庭整体/分层 Agent、单 Agent 与工具接地、角色化多 Agent 和设备/资源/用户 Agent，并以应用任务标签补充能源、照护、安全和个性化等场景。梳理结果表明，近期家庭 LLM 论文以单 Agent 为主，多 Agent 工作则集中在异构设备控制、边缘编排、能源调度、照护和资源约束。两条路线并不矛盾：单 Agent 提供开放式任务理解和跨领域规划，多 Agent 与确定性适配器提供权限隔离、设备协同、冲突处理和故障恢复。

当前最值得关注的方向，不是简单增加 Agent 数量，而是建立可验证的家庭状态表示、能力接口和执行协议，使 Agent 能够在动态环境中安全地规划、执行、监测和恢复。未来研究还需要通过统一的任务定义、多层仿真与真实 testbed、细粒度失败分类和长期用户评测，回答一个更实际的问题：家庭 Agent 是否不仅能生成看似合理的计划，而且能在真实、变化和有风险的家庭环境中持续完成用户真正需要的任务。

## 参考文献

> 参考文献采用顺序编码形式。正式出版物给出会议或期刊出处及 DOI；预印本保留 arXiv 编号和公开链接，并不等同于已同行评审的正式出版结果。

- [H01] Silin Li, Yuhang Guo, Jiashu Yao, Zeming Liu, and Haifeng Wang. “HomeBench: Evaluating LLMs in Smart Homes with Valid and Invalid Instructions Across Single and Multiple Devices.” *Proceedings of ACL 2025*, Long Papers, pp. 12230–12250. [ACL Anthology](https://aclanthology.org/2025.acl-long.597/). DOI: 10.18653/v1/2025.acl-long.597.
- [H02] Gyuhyeon Seo, Jungwoo Yang, Junseong Pyo, Nalim Kim, Jonggeun Lee, and Yohan Jo. “SimuHome: A Temporal- and Environment-Aware Benchmark for Smart Home LLM Agents.” *Proceedings of the International Conference on Learning Representations (ICLR 2026)*, 2026. [Official proceedings page](https://proceedings.iclr.cc/paper_files/paper/2026/hash/43456e781fac3a034842f0807860474a-Abstract-Conference.html).
- [H03] Yi Gu, Huacan Wang, Shuo Zhang, Yuqing Hou, Lei Xue, Weipeng Ming, Chen Liu, Fangzhou Yu, Kuan Li, Ronghao Chen, Sen Hu, Xiaofeng Mou, and Yi Xu. “HomeFlow: A Data Flywheel for Smart Home Agent Training with Verifiable Simulation.” arXiv:2606.01230, 2026. [arXiv](https://arxiv.org/abs/2606.01230).
- [H04] Dmitriy Rivkin, Francois Hogan, Amal Feriani, Abhisek Konar, Adam Sigal, Xue Liu, and Gregory Dudek. “SAGE: Smart Home Agent with Grounded Execution.” arXiv:2311.00772, version 2, 2024. [arXiv](https://arxiv.org/abs/2311.00772).
- [H05] Kuan Li, Shuo Zhang, Huacan Wang, Fangzhou Yu, Zecheng Sheng, Yi Gu, Weipeng Ming, Lei Xue, Chen Liu, Siyue Lin, Yuqing Hou, Xiaofeng Mou, and Yi Xu. “SMH-Bench: Benchmarking LLM Agents for Environment-Grounded Reasoning and Action in Smart Homes.” arXiv:2606.01912, 2026. [arXiv](https://arxiv.org/abs/2606.01912).
- [H06] Manasa Bharadwaj, Yolanda Liu, InJung Yang, Sungil Kim, Nikhil Verma, Ko Keun Kim, Kevin Ferreira, and Youngjoon Kim. “PersonalHomeBench: Evaluating Agents in Personalized Smart Homes.” arXiv:2604.16813, version 3, 2026. [arXiv](https://arxiv.org/abs/2604.16813).
- [H17] Zhonghao Zhan, Krinos Li, Yefan Zhang, and Hamed Haddadi. “HearthNet: Edge Multi-Agent Orchestration for Smart Homes.” *Proceedings of the 1st ACM Conference on Agentic and AI Systems (CAIS ’26)*, 2026, 5 pages. DOI: [10.1145/3786335.3813188](https://doi.org/10.1145/3786335.3813188). Open version: [arXiv:2604.09618](https://arxiv.org/abs/2604.09618).
- [H20] Diane J. Cook, Michael Youngblood, Edwin O. Heierman III, Karthik Gopalratnam, Sira Rao, Andrey Litvin, and Farhan A. Khawaja. “MavHome: An Agent-Based Smart Home.” *Proceedings of the IEEE International Conference on Pervasive Computing and Communications (PerCom 2003)*, 2003. DOI: [10.1109/PERCOM.2003.1192783](https://doi.org/10.1109/PERCOM.2003.1192783).
- [H21] Sajal K. Das and Diane J. Cook. “Health Monitoring in an Agent-Based Smart Home by Activity Prediction.” In D. Zhang and M. Mokhtari (eds.), *Toward a Human-Friendly Assistive Environment*, Assistive Technology Research Series 14, IOS Press, 2004, pp. 3–14. ICOST 2004. [Author version](https://eecs.wsu.edu/~cook/pubs/icost04.pdf).
- [H22] Qinglong Wu, Fei-Yue Wang, and Yuetong Lin. “A Mobile-Agent Based Distributed Intelligent Control System Architecture for Home Automation.” *Proceedings of the IEEE International Conference on Systems, Man and Cybernetics*, 2001, pp. 1599–1605. DOI: [10.1109/ICSMC.2001.973521](https://doi.org/10.1109/ICSMC.2001.973521).
- [H23] Shadi Abras, Stéphane Ploix, Sylvie Pesty, and Mireille Jacomino. “A Multi-agent Home Automation System for Power Management.” In *Lecture Notes in Electrical Engineering*, vol. 15, Springer, 2008, pp. 59–68. DOI: [10.1007/978-3-540-79142-3_6](https://doi.org/10.1007/978-3-540-79142-3_6).
- [H24] Qingquan Sun, Weihong Yu, Nikolai Kochurov, Qi Hao, and Fei Hu. “A Multi-Agent-Based Intelligent Sensor and Actuator Network Design for Smart House and Home Automation.” *Journal of Sensor and Actuator Networks*, 2(3), 2013, pp. 557–588. DOI: [10.3390/jsan2030557](https://doi.org/10.3390/jsan2030557).
- [H25] Song Zheng, Qi Zhang, Rong Zheng, Bi-Qin Huang, Yi-Lin Song, and Xin-Chu Chen. “Combining a Multi-Agent System and Communication Middleware for Smart Home Control: A Universal Control Platform Architecture.” *Sensors*, 17(9), 2017, 2135. DOI: [10.3390/s17092135](https://doi.org/10.3390/s17092135).
- [H26] Salama A. Mostafa, Saraswathy Shamini Gunasekaran, Aida Mustapha, Mazin Abed Mohammed, and Wafaa Mustafa Abduallah. “Modelling an Adjustable Autonomous Multi-Agent Internet of Things System for Elderly Smart Home.” In *Advances in Neuroergonomics and Cognitive Engineering*, Advances in Intelligent Systems and Computing 953, Springer, 2020, pp. 301–311. First published online 2019. DOI: [10.1007/978-3-030-20473-0_29](https://doi.org/10.1007/978-3-030-20473-0_29).
- [H27] Ferdinando Fioretto, Agostino Dovier, and Enrico Pontelli. “Distributed Multi-Agent Optimization for Smart Grids and Home Automation.” *Intelligenza Artificiale*, 12(2), 2019, pp. 67–87. DOI: [10.3233/IA-180037](https://doi.org/10.3233/IA-180037).
- [H28] Lysa Gramoli, Julien Cumin, Jérémy Lacoche, Anthony Foulonneau, Bruno Arnaldi, and Valérie Gouranton. “Generating and Evaluating Data of Daily Activities with an Autonomous Agent in a Virtual Smart Home.” *ACM Transactions on Multimedia Computing, Communications, and Applications*, 21(1), Article 13, 2025; published online 23 December 2024. DOI: [10.1145/3665331](https://doi.org/10.1145/3665331).
- [H29] Evan King, Haoxiang Yu, Sangsu Lee, and Christine Julien. “Sasha: Creative Goal-Oriented Reasoning in Smart Homes with Large Language Models.” *Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies*, 8(1), 2024. Related DOI: [10.1145/3643505](https://doi.org/10.1145/3643505). Open version: [arXiv:2305.09802](https://arxiv.org/abs/2305.09802).
- [H30] Chaerin Yu, Chihun Choi, Sunjae Lee, Hyosu Kim, Steven Y. Ko, Young-Bae Ko, and Sangeun Oh. “Leveraging LLMs for Efficient and Personalized Smart Home Automation.” arXiv:2601.04680 [cs.HC], submitted 8 January 2026. DOI: [10.48550/arXiv.2601.04680](https://doi.org/10.48550/arXiv.2601.04680). [arXiv](https://arxiv.org/abs/2601.04680).
- [H31] Eu Jin Lim, Zhaoxing Li, and Sebastian Stein. “AdaHome: An Adaptive Smart Home Assistant using Local Small Language Models.” arXiv:2607.18034v2 [cs.AI], submitted 20 July 2026, revised 22 July 2026. DOI: [10.48550/arXiv.2607.18034](https://doi.org/10.48550/arXiv.2607.18034). [arXiv](https://arxiv.org/abs/2607.18034).
- [H32] He Zhang, Feilong Li, Dingning Long, Yilin Cui, Peijun Zhang, Yuewen Zhang, Qianyao Xu, and Xinyi Fu. “PromptShield Home: Ambient Multimodal Prompt Injection Defense for Smart-Home Agents.” arXiv:2608.05495, 2026. [arXiv](https://arxiv.org/abs/2608.05495).
- [H33] Akila Siriweera, Janani Rangila, Keitaro Naruse, Incheon Paik, and Isuru Jayanada. “S5-HES Agent: Society 5.0-driven Agentic Framework to Democratize Smart Home Environment Simulation.” arXiv:2603.01554v1 [cs.AI], submitted 2 March 2026. DOI: [10.48550/arXiv.2603.01554](https://doi.org/10.48550/arXiv.2603.01554). [arXiv](https://arxiv.org/abs/2603.01554).
- [H34] Soledad Valero, Elena del Val, José Alemany, and Vicente Botti. “Using Magentix2 in Smart-Home Environments.” In Álvaro Herrero et al. (eds.), *10th International Conference on Soft Computing Models in Industrial and Environmental Applications (SOCO 2015)*, *Advances in Intelligent Systems and Computing*, vol. 368, pp. 27–37, Springer, 2015. DOI: [10.1007/978-3-319-19719-7_3](https://doi.org/10.1007/978-3-319-19719-7_3).
- [H35] Dagmawi Neway Mekuria, Paolo Sernani, Nicola Falcionelli, and Aldo Franco Dragoni. “Smart Home Reasoning Systems: A Systematic Literature Review.” *Journal of Ambient Intelligence and Humanized Computing*, 12, 4485–4502, 2021; published online 15 November 2019. DOI: [10.1007/s12652-019-01572-z](https://doi.org/10.1007/s12652-019-01572-z).
- [H36] Pedro Filipe Oliveira, Paulo Novais, and Paulo Matos. “Smart Environment: Using a Multi-agent System to Manage Users and Spaces Preferences Conflicts.” In Kohei Arai (ed.), *Intelligent Computing. SAI 2023*, *Lecture Notes in Networks and Systems*, vol. 711, pp. 1361–1377, Springer, 2023. DOI: [10.1007/978-3-031-37717-4_90](https://doi.org/10.1007/978-3-031-37717-4_90).
- [H37] Marjan Alirezaie, Jennifer Renoux, Uwe Köckemann, Annica Kristoffersson, Lars Karlsson, Eva Blomqvist, Nicolas Tsiftes, Thiemo Voigt, and Amy Loutfi. “An Ontology-based Context-aware System for Smart Homes: E-care@home.” *Sensors*, 17(7), 1586, 2017. DOI: [10.3390/s17071586](https://doi.org/10.3390/s17071586).
- [H38] Nasser Alshammari, Talal Alshammari, Mohamed Sedky, Justin Champion, and Carolin Bauer. “OpenSHS: Open Smart Home Simulator.” *Sensors*, 17(5), 1003, 2017. DOI: [10.3390/s17051003](https://doi.org/10.3390/s17051003).
- [H39] Noel Nuo Wi Tay, János Botzheim, and Naoyuki Kubota. “Weighted Constraint Satisfaction for Smart Home Automation and Optimization.” *Advances in Artificial Intelligence*, 2016, Article 2959508, 15 pages. DOI: [10.1155/2016/2959508](https://doi.org/10.1155/2016/2959508).
- [H40] Zhaozong Meng and Joan Lu. “A Rule-based Service Customization Strategy for Smart Home Context-Aware Automation.” *IEEE Transactions on Mobile Computing*, 15(3), 558–571, 2016. DOI: [10.1109/TMC.2015.2424427](https://doi.org/10.1109/TMC.2015.2424427).
- [H41] Maria J. Santofimia, David Villa, Óscar Aceña, Xavier del Toro, Carlos Trapero, Felix J. Villanueva, and Juan Carlos López. “Enabling Smart Behavior through Automatic Service Composition for Internet of Things-based Smart Homes.” *International Journal of Distributed Sensor Networks*, 14(8), 2018. DOI: [10.1177/1550147718794616](https://doi.org/10.1177/1550147718794616).
- [H42] Devleena Das, Yasutaka Nishimura, Rajan P. Vivek, Naoto Takeda, Sean T. Fish, Thomas Plötz, and Sonia Chernova. “Explainable Activity Recognition for Smart Home Systems.” *ACM Transactions on Interactive Intelligent Systems*, 13(2), Article 7, 2023, pp. 1–39. DOI: [10.1145/3561533](https://doi.org/10.1145/3561533). [ACM full text](https://dl.acm.org/doi/fullHtml/10.1145/3561533).
- [H43] Amina Jarraya, Amel Bouzeghoub, Amel Borgi, and Khedija Arour. “DCR: A New Distributed Model for Human Activity Recognition in Smart Homes.” *Expert Systems with Applications*, 140, 112849, 2020. DOI: [10.1016/j.eswa.2019.112849](https://doi.org/10.1016/j.eswa.2019.112849).

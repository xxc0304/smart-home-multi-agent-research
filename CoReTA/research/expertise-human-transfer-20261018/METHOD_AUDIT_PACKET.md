# 专家专长利用机制：查新与可行性审查输入
日期2026-10-18。用户ACL2027目标；已有API工程能力，不假定有GPU/RL预算；本轮只审查不实验。

## 冻结的构想（评这个整体，不能把组件相似当重复）
目标：可靠利用互补专家提升团队任务成功率。成员先独立给答案/知识支点；协调器定位决定性分歧；接收者指出自己不接受/无法使用的具体前提或步骤；相关成员围绕此障碍提供针对性知识、局部推导或反例/测试；接收者独立应用/检查后更新自己的贡献，再完成共同决策。专家不是固定真值，可被反证纠正。专家可依据独立开发集能力定义，测试正确性仅作事后标签。
候选delta：针对当前接收者障碍的双向知识转移，改善已在团队内的专长从“有人掌握”到“他人能正确使用”的过程。不能把更长解释、更多token或更强裁判当机制。若只有三人意见聚合，直接选expert可能更便宜，因此需考虑下游由不同成员继续推理/执行的真实需求，但不能人为禁止合理基线选expert。
主张C1：已有能力优势没被利用，是可改变的组织问题。
C2：接收者当前障碍用于决定专家补充什么，优于普通解释/提问。
C3：接收者应用反馈改变后续交互，避免口头同意充作理解/正确。
C4：提高正确专长利用且不增加错误专家盲从，并在预算匹配完整任务中获益。
没有新方法实测数据；旧智慧家庭实验不是本方法的证据。

## 本轮实质核读最近邻（下列不得写成逐字精读或代码复现）
1. Multi-Agent Teams Hold Experts Back, Pappu et al., ICML2026 https://arxiv.org/html/2602.01011v4 。专家已知仍可能被稀释。ALOC逐题oracle不等于固定最强。其一般问题非首次。
2. SAT, Pappu et al., 2026-09-19预印本 https://arxiv.org/html/2609.22682v1 。离线学习冻结可迁移协作策略；证书+逐项具名缺陷审计；组合部分推理。研究目标不同，但保护正确少数、审计、知识组合已有。跨基准demonstrability关联，不等于已测同题接收者适配干预。
3. Large Language Models are In-context Teachers for Knowledge Reasoning, Zhao et al., Findings EMNLP2024 https://arxiv.org/html/2311.06985v3 。Teach-Back在500个训练样本的学生自解释上LoRA调教师，教师生成更适配学生的ICL示范，随后学生解新题。不是本次在线团队共决策。组件理念相近不是否决；“让学生复述后当场改解释”不是该文准确概括。
4. Socratic Skill Learning: Interleaving Teaching and Practice for Transferable Agent Skills, Letian Zhu et al., 2026-10-13预印本 https://arxiv.org/html/2610.17860v1 。§4.1 Educator可解释/挑战/诊断/提检查/沉默，Student可质疑/测试/适配/拒绝建议；Student独自操作环境并写可迁移Skill；Issue-Guided版维护未解决学习问题指导选择和聚焦review。输出Skill给fresh solver做跨实例迁移。此为比TeachBack更直接的机制近邻，但固定Educator/Student、技能获取目的不同；不能把问题驱动解释+实践验证称首次。
5. KAMAC, Wu et al., EMNLP2025 https://arxiv.org/html/2509.14998 。§3 检测团队知识缺口后动态招聘新的医学专家，持续讨论直到共识或限轮，moderator最终决策。作用于缺失专业知识/专家招募，非核心研究已有专家知识如何被接收者正确使用。不能据“knowledge gap”同名判重复。
6. SEIMAD: Socratic Elenchus-inspired multi-agent debate for mitigating hallucinations in large language models, Jiacheng Huang/Tao Han/Ning Yu/Xiaoyin Yi, ESWA320 132208, 2026-07-15, DOI10.1016/j.eswa.2026.132208 https://www.sciencedirect.com/science/article/abs/pii/S0957417426011218 。原出版机构搜索索引取到了完整摘要/引言；直接访问403。assistant/critic/judge，初答→迭代苏格拉底质询→final judgment，质询假设/定义/推理步骤并提反例；目标hallucination correction。完整方法/提示和实验未取，不能声称其缺少接收者建模或专家利用度量，属于需补全文的近邻。不应因为它叫提问就否定整体。
7. When Debate Helps: Proposal Supply and Verification-Aware Readout in Multi-Agent Reasoning, Zihao Zhao et al., 2026-10-03预印本 https://arxiv.org/html/2610.04686v1 。§摘要/引言：recoverable headroom(有正确候选但多数错)；Latent Verification Debate作为accounting model，固定候选干预正确证据、测读出概率和决策；coverage-selected neural thicket society。改善覆盖+truth sensitive evidence use已经研究，固定候选因果干预也不能独占。非已确认同一个receiver-specific互动算法。
8. Adaptive Theory of Mind for LLM-based Multi-Agent Coordination, Mu et al., AAAI2026/arxiv2603.16264 https://arxiv.org/html/2603.16264 。依历史推断partner ToM推理阶数并适配行动，矩阵game/navigation/Overcooked，非逐主张专家知识传递。身份品牌不等同真实专长。
9. Talk is Cheap, Communication is Hard: Dynamic Grounding Failures and Repair in Multi-Agent Negotiation, Yao/Zou/Hawkins, 2026-05 v2 https://arxiv.org/html/2605.01750 。研究资源谈判共同理解/承诺/执行失败与修复；不是已证实本方法，但说明“沟通成功≠知识被正确使用”不是首提。
10. Augmenting Multi-Agent Communication with State Delta Trajectory, Tang et al., EMNLP2025 https://aclanthology.org/2025.emnlp-main.518/ 。把推理状态增量编码为自然语言通信补充，隐状态访问依赖，非本黑盒API接收者障碍协议；本轮摘要核验。
11. 原有邻居ReConcile/ConfMAD(置信加权)、CoThinker/MATM(TMS)、HiddenBench(交换后决策)、MARCH盲检、AgentAuditor局部分歧审计：详见research/expertise-human-transfer-20261018/AGENT_PRIOR.md，本轮未全部重读。
12. 人类干预Bonner/Baumann2012、Bonner/Bolinger2013：相关知识提取改善群体输入加权，是可检验设计动机而非LLM因果证据。

## 检索边界
本轮广搜+同义词查新30余关键词(见后续台账)，覆盖arxiv/ACL/OpenReview/AAAI/出版方；重点补最近6个月。不能承诺未来永不发现邻居。未核所有代码和闭源全文。大学库SEIMAD摘要尾部误混磁材料文本，已弃用，以出版社索引摘要替代。预印本不冒充已录用。

## 请审核
你是fresh同家族独立上下文审查者。请基于上述材料并可联网补查(不跑实验)，回答：
1. 用户认为TeachBack只是部分组件相似是否正确？不要迎合，也不要把所有交集当重复。
2. 没有哪个已核论文完整包含构想时，不得ABANDON；若delta太薄，指出具体的缺项。
3. 当前构想是否已能称方法，还是需形式化操作？推荐最小修改，禁止换研究主线。
4. 最危险可行性缺陷：接收者不能正确自报障碍/无法验证专家，局部适配只是说服，固定专家和实际互补专家混淆，代价超过直接调用强者；给可执行对照。
5. 给“现在是否值得做小试”的明确结论与go/no-go，而非永远需要检索。评ACL潜力，不给录用概率。
6. 证据中哪些是未读全文，不能用其不存在某组件作新颖性证据。
输出中文1000-1800字，独立评价，勿新增付费请求。


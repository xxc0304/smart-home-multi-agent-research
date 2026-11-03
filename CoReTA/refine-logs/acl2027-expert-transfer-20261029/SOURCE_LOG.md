# 本轮材料访问与检索范围

检索及核查日期：2026-10-29。当前对话的可见历史、项目文档与下列可访问材料构成依据；没有声称读完全部历史聊天或全部83篇文献。

## 上下文与存量证据

- 阅读 CoReTA/AGENTS.md、handoff.md、CURRENT_STATE.md最新条目、brainstorm.md、submission/ACL_2027.md、related_work/INDEX.md。
- 阅读 research/expert-team-novelty-recheck-20261029/REPORT.md 与 RESEARCH_START.md、WHY_SIMILAR_METHODS_DIFFER.md、004/019复核；独立资料恢复者进一步核对8条历史路线及其原始结果。
- 通过应用 read_thread 实际访问“CoReTA”（01a14f14-e3fa-7d60-b8be-6e1f9be4f2f5）最近5轮和“解析多智能体预测论文”（01a182c3-2c89-7bb1-ba8f-b13e8a5eaa5d）最近4轮。范围仅这些页，未遍历更早所有轮次。后者的9−4四agent例子明确是教学虚构，不进入实证。
- 用PDF提取工具核对本地6篇首3页及元数据：2602.01011v4、2410.14596v2、2609.22682v1、2610.04686v1、2610.01042v1、2510.10185v3；核心方法和结果进一步通过arXiv/会刊指定段落核查，未逐字通读全部97页MedAgentAudit。

## 主要原始来源与核查内容

| 来源 | 状态和本轮核查范围 |
|---|---|
| https://2027.aclweb.org/calls/main/ | ACL2027官方CFP、日期、篇幅、主题、ARR路径；并非借用往届截止日 |
| https://aclrollingreview.org/cfp | 当前正文长度、Limitations、服务登记及投稿要求 |
| https://aclrollingreview.org/reviewerguidelines | 研究贡献类型、公平评价、soundness/excitement及常见缺陷 |
| https://aclrollingreview.org/acguidelines | main/Findings区别；接收须可靠，创新/影响/兴趣非单一硬阈值 |
| https://aclrollingreview.org/sustainable-reviewing-2026 | 当前评审容量与合格service contributor规则，实施仍可能更新 |
| https://arxiv.org/html/2602.01011v4 | 表2及5、§4.3–4.5、附录J；专家定义、ALOC与固定强者的区别 |
| https://github.com/apappu97/multi-agent-teams-hold-experts-back | 经GitHub连接器核对根目录、README、conversation.py及两种collaborative task源代码；MC execute保存独立全文与团队全文，reveal_expert用当题gold判断。只见公开代码与日志设施，未确认论文完整原始运行日志可下载 |
| https://aclanthology.org/2025.naacl-long.412/ | PBT正式NAACL2025论文，强弱配对、正负说服平衡及训练 |
| https://arxiv.org/html/2609.22682v1 | SAT §4表1/2、§5 demonstrability，案例与跨任务相关/任务内干预的区别 |
| https://arxiv.org/html/2610.04686v1 | When Debate Helps §5和A.9，供给与读出、固定候选干预 |
| https://arxiv.org/html/2610.01042v1 | ICR §1/3/4，正确保留与纠错、无消息对照、内容和接收策略 |
| https://arxiv.org/pdf/2510.10185v3 | MedAgentAudit专家角色和过程审计，沿用已核§4.4与本轮PDF首3页，不声称已重新通读全部 |
| https://arxiv.org/html/2609.38964v1 | 新补When Order Matters §3–5、附录C/I，真实强弱/顺序/宜人性；提升强者影响并非单调提升准确率 |
| https://aclanthology.org/2025.findings-emnlp.335/ | 新补OSC；正式元数据和PDF§3/4由文献侦察者核查；作者列表以最终PDF核对，暂以题名引用 |
| https://onlinelibrary.wiley.com/doi/10.1111/exsy.70392 | 新补Are Agents Listening；出版社摘要和数据声明，付费全文本轮未读；使用修订后426 unique DPs/793条件的口径，不沿用README旧数 |
| https://github.com/oldblack45/listening-agents/releases/tag/revision3-review-v1 | 作者修订资产入口，未把可访问页面等同完整资产本地验证 |
| https://aclanthology.org/2026.findings-emnlp.387/ | 新补EDGE正式版本状态；arXiv正文§3及附录A.2区分真实rollout与模拟续写；未下载原始数据 |
| https://arxiv.org/html/2608.23541v1 | 新补Interaction Tax；11个验证器任务、同预算、完整方案交流与多样性，以及敏感性边界 |
| https://aclanthology.org/2026.emnlp-main.1780/ | GDP/CARA正式EMNLP2026；过程指标贡献先例，不以总准确率提升为唯一论文价值 |
| https://aclanthology.org/2026.findings-acl.1600/ | Free-MAD正式FindingsACL2026；反从众和轨迹读出先例 |
| https://github.com/StonyBrookNLP/musique | 数据/官方评分/CC BY4.0，种子问题泄漏警告；候选数据，未下载核验全部样本 |
| https://hotpotqa.github.io/ | HotpotQA主数据候选；官方支持事实、EM/F1评分及CC BY-SA4.0；经第2轮审查替代无材料QA作为主D对比，数据尚未下载核验 |
| https://github.com/TIGER-AI-Lab/MMLU-Pro | 领域QA及评分候选；不直接采用允许retry_wrong的便利脚本，任何gold触发重试不进入生成协议 |
| https://api-docs.deepseek.com/quick_start/pricing/ | 官方峰时cache-miss Flash $0.30/$1.20、Pro $1.32/$3.96，每百万输入/输出token；模型别名及实际版本变化 |
| https://www.alibabacloud.com/help/en/model-studio/model-pricing | 2026-10-29官方国际价qwen3.8-max-0902 $2/$6每百万；地区/模式/缓存须分别核对 |

## 实际定向检索

三组各三条（文献侦察者执行），后续按题名/正文引文追踪：

1. `multi-agent expert weaker stronger agents collaboration capability 2025 2026 ACL EMNLP ICML`
2. `"LLM" "multi-agent" "expertise" "communication" "selection" 2026`
3. `"Multi-Agent Teams Hold Experts Back" "SAT"`
4. `"multi-agent" "error attribution" "communication" 2025 2026 ACL`
5. `"AgentInteractError" OR "MedAgentAudit" OR "When Debate Helps"`
6. `"multi-agent" "correct" "selection" "capability" 2026 ACL EMNLP`
7. `"LLM" "persuasion" "correct" "incorrect" 2025 2026 NAACL ACL`
8. `"multi-agent" "error correction" "contamination" "2026"`
9. `"Beyond Final Accuracy" OR "Who Becomes an Influencer" OR "PBT" "debate"`

主执行者另检索：ACL2027官方CFP、ARR reviewer guidelines；`LLM multi agent expert demonstrability evidence clarity authority controlled experiment 2026`；`multi agent expertise preservation causal communication bottleneck verification intervention 2025 2026`；`"expert" "counterfactual" "multi-agent" "2026"`；`"multi-agent" "demonstrability" intervention`；`"LLM" "expert" "evidence quality" "authority" debate`等，并在arXiv、ACL Anthology、PMLR及作者仓库核对。

## 覆盖局限与失败访问

- 时间重点2025–2026、尤其2026年5–10月，并追踪最直接先行工作；不是领域穷尽系统综述或独立全文数据库检索。
- arXiv API helper已解析并尝试查询，终端网络因WinError10013无法连接；改用web检索与arXiv原文。未借此声称API检索成功；无自动审批拒绝。
- 未连接Zotero/Obsidian/Semantic Scholar等专门数据库；不假定已覆盖这些库。没有调用Gemini/Exa付费检索。
- NMI `https://www.nature.com/articles/s42256-026-01268-y` 全文重定向失败，只有文献侦察者核过的搜索/出版信息，本轮不据此建立关键机制结论。
- 一次误试Anthology .937返回TRIO而非EDGE，已识别并舍弃，EDGE以核实的.387为准。
- 未找到某主张的单篇覆盖不构成首创证明；新颖性以拟议的实证发现及最接近工作逐项比较。

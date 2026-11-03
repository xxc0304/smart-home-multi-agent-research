# 补充近邻：已有前提的依赖探测与局部修复

日期：2026-10-20。两轮定向检索：先搜conditional answers / assumption dependency / counterfactual clarification / partial knowledge，再追踪正式ACL条目和作者方法全文。下面两项为本轮新补入，不冒充此前已经完成的查新。无代码执行或模型实验。

## 1. SAVeR：Verify Before You Commit: Towards Faithful Reasoning in LLM Agents via Self-Auditing

Wenhao Yuan等，ACL 2026主会。[正式条目](https://aclanthology.org/2026.acl-long.1440/)，[正式PDF](https://aclanthology.org/2026.acl-long.1440.pdf)。已读§3、表3与附录A–C的审计/修复提示。

它在单个agent内部生成多种persona候选信念，选取结构多样的推理轨迹，审计缺失假设/错误前提等局部问题，给出具体探针和接受条件，再只修失败片段并复查后提交。其counterfactual repair指局部编辑，不等于对同一未知变量取多个合法值来识别依赖。表3中审计与修复主要改善推理忠实性指标，对EM/F1影响有限，不能据此说其组件已证明端到端互补增益。

与CoReTA重叠：隐含前提定位、保留未受影响推理、按具体条件复查。差别：内部persona不等于具有不同私有信息的成员；本文所读方法没有以跨成员补足条件关系作为组织控制对象。CoReTA不能将“局部审计修复”重新包装首创，仍要定义不同的信息与决策机制。

## 2. StateWise：Diagnosing and Repairing Persistent Operational State Before Agent Actions

Yongyuan Peng等，arXiv:2610.05241v1（2026-10-04）；本轮仅确认预印本，不标正式录用。[作者全文](https://arxiv.org/html/2610.05241v1)。已读§3–4。

它临时改变/移除已有记忆记录，比较行动变化以定位决策关键前提，再用当前环境只读检查或向开发者澄清取得证据，修正具有明确范围的持久记录并重新规划。影响性与有效性分开，扰动本身不证明记录错误。

与CoReTA重叠：保持其余输入不变的前提探测、定向补证据及局部更新。差别：已有显式记录→行动归因与持久修复，不等于发现成员未表达的条件、恢复条件关系再交给互补成员实例化。若我们的实现最后仅删一条记录看答案变不变，再查该记录，操作就非常接近它，不能只靠多几个agent区分。

## 3. 未纳入的线索

EPRAG的出版方页面本轮正文访问失败，不根据搜索摘要推断其具体方法或作为确认重叠。Corollary是作者项目仓库，不能当同行评审论文；其依赖消融宣称没有在本轮做实现核验，不借其保证。二者不用于主报告新颖性裁决。

## 4. 综合边界

SAVeR修理已经形成的推理；StateWise追查已经写入的前提。二者提示我们，发现依赖、核实事实、限制更新范围是不同操作。它们为CoReTA提供具体比较，不能据标题中的counterfactual将三种机制混为一谈。当前候选的“新条件从哪里来”仍未被这些方法自动替代或被CoReTA自身解决。

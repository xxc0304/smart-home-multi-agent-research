# 局部优势校准准备进度

## 本次修正后的最新状态

已补齐运行器tools/run_local_judgment_calibration.py，并生成独立r2冻结包：runs/local-judgment-moon-calibration-prepared-20261025-r2。21项相关测试通过，24步完整模拟和48份历史公共接口回放通过；输入估计最大1511/8192、适配输出910/1536。本地研究意义与准备均PASS。新任务真实模型回复仍为0，模拟不计作能力结果。

r2已保存EXPERIMENT_REVIEW.md/json、PREFLIGHT.json、TEST_EVIDENCE.json，绑定manifest。r1及下文为修改前准备记录，不能据其状态启动。当前只缺本批具体授权；没有执行付费请求，也未创建授权文件。预算固定最多24次、零重试、首错停止，不自动扩跑。

---

以下为修正前的准备记录。

本次把任务候选落实为一组有限的月球练习资源校准。6个局部问题、3个原资料持有者、每项有/无资料两条件各2次，拟24请求。没有模型实验，也没有新架构效果。

## 已完成

- 设计题目：local_judgment_calibration_moon_items.json。问题不预填正确用途，不要求完整排名。问题人工给定的限制公开。
- 离线准备器：tools/prepare_local_judgment_calibration.py，仅支持构包，无run或模型客户端。
- 评分口径：LOCAL_JUDGMENT_MOON_CALIBRATION_RUBRIC_20261025.md，核心、依据、范围扩张分开，允许无资料组凭已有知识答对。
- 12份请求模板、24个拟运行槽位：runs/local-judgment-moon-calibration-prepared-20261025-r1。
- 14项本地测试通过；6对输入仅资料有差别；3份上游快照hash一致；最大指令估计922 tokens。
- 本批EXPERIMENT_REVIEW.md：意义PASS（仅校准），准备BLOCKED，总体DO_NOT_RUN。

## 没有完成也没有声称

- 这些问题不代表六个独立情景，不支持跨任务专长结论。
- 没有观察到有资料比无资料更好，未排除知识天花板。
- 没有验证自主选题或整合采用；原H1的普通评议与自主提问对照尚未运行。
- 没有本批联网执行器、真实新任务回复或最终启动审核。旧70次授权不适用本批。

下一步是将本校准接入最小有界执行器，检查首错停止、原始响应/usage保存、部分结果导出及最终冻结；全部通过后再按用户授权执行。若校准不形成优势，则不把这组题当作已验证专长条件继续搭架构。

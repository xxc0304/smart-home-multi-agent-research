# 构建进度

| Rung | 内容 | 验收 | 状态 |
|---|---|---|---|
| F0 MUST | 命令→fixture产物 | smoke，exit0/52记录 | PASS |
| F1 MUST | 两轮/四分支信息边界 | 7项protocol checks | PASS |
| F2 MUST | 投票/指标/配对与失败 | 6项scoring checks | PASS |
| F3 MUST | 本地模型入口/资格/预算 | 9项runtime checks+offline check | PASS（离线范围） |
| F4 MUST | 真实D接口/文档/假设审查 | 32输入检查+两轮fresh sweep/修订回归 | PASS离线；模型审查provisional |

## 边界

保留旧四轮程序，复用B0 helper；根工作树有既有未提交内容，不初始化/重置或提交无关文件；fresh审查直接读本阶段文件列表，空git diff不当作覆盖。
真实实验、专家训练/资格、GPU模型兼容、正式预算均未运行。

## 执行记录

- F0：CLI写完整52事件手写fixture，exit0，真实模型调用0；在F1前已完成。
- F1/F2：unittest 12项，exit0。修正一处测试预期：官方规范化会去英文冠词A，改用alpha/beta验证一般票型，不改官方评分。
- F3：累计19项B1 unittest，exit0，含真实随机tiny CPU生成、PEFT开关、mock完整52请求/接续、OOM、C绑定与待填配置拒绝。不是Qwen任务实验。
- 回归：B0 9项，exit0；临时tiny两步训练/重载是工程测试，无MuSiQue训练。
- D接口：固定32输入、29关系组，1664预期请求；不读D gold/C/H题文，当前真实配置BLOCKED。
- 第一轮fresh假设审查6项未登记/4项不一致，原始JSON保留。修复原文双重清理/C题序/前缀解析/阶段接续/首遍seed，补固定M1与显式top_k/中性解码、成员诊断/实际读出损失/题级敏感性CI、CUDA峰值和模板异常停批。累计22项B1检查exit0；审查触发了3项回归测试。中性GenerationConfig在安装版本的num_beams默认None，一项新检查失败后明确设1，未改研究对照。
- 第二轮无新未登记、3项stale：执行者随后同步中性配置至PEFT/底座、模板边界捕获Jinja错误、加载前重置及finally记录CUDA峰值。新增用例中手写checkpoint min_p需do_sample=true才合法保存，修正fixture后最终B0+B1共31项exit0（7.259秒）；CPU模板停批/配置重置实测，CUDA峰值逻辑未实机测量。无第三轮fresh，保留same-family/provisional，不改写原审查为clean。
- 未提交：工作树有大量既有未提交/未跟踪研究资产；为避免混入或覆盖，不做阶段git提交。fresh审查使用本阶段实际文件列表，不以空diff代替。

## Deferred

真实GPU/Qwen/4bit/长上下文/峰值显存和完整讨论链验收；真实专家训练/校准；更大N与重复/资源合同。等待实际设备和研究证据，不用新增文献/数据审核替代。

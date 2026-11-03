# 独立诊断适配器与离线验收

## 已交付

- `tools/sbp_diagnostic.py`：prepare/check/run三种入口。默认不调用模型；run要求显式--live、API环境配置、冻结准备包及全新输出目录。固定36单元，异常单元结束后停批；内容答错本身不作为停批条件。离线评分文件不由适配器读取。
- `tools/check_sbp_diagnostic.py`：注入脚本transport的离线验收，明确标记scripted_not_model_result，所有usage均为脚本值，不作真实用量或能力证据。
- 最终准备包：`runs/sbp-diagnostic-v1-prepared-20261021-r3/`，36份首请求、输入packet、schema、配置/预算、输入估计及源码哈希。只预生成首请求，后续依赖真实输出，不能提前冻结其文本。
- 完整路径验收：`runs/sbp-diagnostic-v1-scripted-20261021-r2/acceptance.json`，40场景通过，real_network_requests=0。包含36正常单元，以及CoReTA格式恢复、传输重试、截断恢复、中断保存四场景。
- 静态验收：最终准备包`acceptance.json`，确认D1同数据、D2同公开内容、成员原始权限、原始事实保留、17引用容量及非法/重复引用拒绝。

## 明确的实施选择

1. D1两臂packet均将DIRECTORY设为空数组。贡献模板必须有此键，独立模板仍省略该键；两边不提供目录事实。原方案写“不含DIRECTORY”，现记录这一接口选择，不引入信息差。
2. D2普通讨论PUBLIC_DISCUSSION与CoReTA CONTRIBUTIONS起始内容对象逐字段相同。A1仍独占原始S权限，其他成员只能用公开C；普通讨论的引用索引也列出可见C。初始候选统一取C5中A2的共享排序，不从答案文件挑选。
3. 固定输入是人工编写的7条C，其中A1四条分候选消息。这是受控注入，不冒充原协议自然生成的“最多三条贡献”。真实初始生成诊断仍使用原三条上限。不得把注入诊断直接当成自然端到端方法成绩。
4. 引用容量仅在独立DiagnosticContracts中将Refs.maxItems从12改为当前可见引用数；保留可见枚举与去重。APPLY的bindings等其他结构上限不改。两项诊断统一使用该容量适配，不能把未来结果与旧12上限结果当作单因素对照。
5. 没有恢复旧版知识保留措辞，没有增加检查指令，没有修改角色路由、阶段语义或停止规则。原冻结实验清单中26文件哈希全部一致。
6. 单步贡献结果明确记录diagnostic_initial_outputs及complete_ranking_required=false，不将没有完整排序认作贡献交付失败。

## 准备期间发现并处理的问题

最初prepare因旧贡献渲染器需要DIRECTORY键而停止，零网络。第一目录留下不完整准备文件，不能用于运行。之后r2准备完成；进一步补了初始结果标注、中断落盘、重复引用专门检查，再生成最终r3。r2准备包源码哈希已过期，check会拒绝；保留历史，不覆盖旧包。

## 运行命令（本轮未执行run）

在项目根目录CoReTA下，使用本项目Python：

```powershell
.venv/Scripts/python.exe tools/sbp_diagnostic.py check --prepared runs/sbp-diagnostic-v1-prepared-20261021-r3
.venv/Scripts/python.exe tools/sbp_diagnostic.py run --prepared runs/sbp-diagnostic-v1-prepared-20261021-r3 --output runs/sbp-diagnostic-v1-live-20261021 --live
```

run的所有真实请求由既有Gateway记录，日志保留完整instructions/schema及响应；不会调用评分器。36单元固定顺序，最坏288次HTTP，不代表实际消耗。

## 验收边界

脚本验收证明已覆盖的调度、接口与恢复路径可运行，不证明真实模型会遵循协议，不保证不再出现格式错误，也未复验服务端对新动态引用上限的接受情况。上下文大小仅对首请求作离线估计，后续仍由既有Gateway逐次限制。单元恢复与中断已脚本检查，完整批次真实停批路径尚无真实模型证据。

目前可以进入固定方案的真实诊断；它仍是开发诊断，不能作为CoReTA有效或失败的统计结论。本轮真实请求0。

# 来源绑定 v2：修改与离线验证

日期：2026-10-20。条件：`task_audit_binding_v2`，契约：`coreta/0.7-source-binding`。状态：修改及本地验证完成。外部模型请求0；尚未执行v2的140真实回归。

## 已完成的修改

新增 `src/coreta/task_audit_binding.py` 和独立入口 `python -m coreta.run_task_audit_binding`，通过继承复用v1的候选、issue、审计保留与B→U→C流程。v1冻结源文件、提示和原始失败结果保留。调度仍为三初稿、一次事实提取、综合及最多三轮B/U/C，共最多14次逻辑调用，不增加final。

### 来源绑定

模型输出fact_id、白名单source_id、原文quoted_text、解释、类型和声明的check_items，不再生成字符位置或JSON Pointer。数学任务的来源注册表只有prompt；代码任务有有效entry_point时才额外提供该字段。task_type、task_id和空entry_point不作为提取事实的来源。

程序对解码后的原始字符串做精确匹配：

- 唯一匹配：分配Unicode字符跨度及公共字段路径，标记unique_exact。
- 多次匹配：标记ambiguous，不选第一处，反馈需要更完整上下文。
- 无匹配或来源不可用：标记unmatched/unknown_source，逐条反馈。

不去空格、删标点、改写公式或做模糊匹配。模型原始响应与程序派生位置分别保存。来源已绑定只证明引文出自该位置；解释和检查项始终标记model_asserted。

### 定向修复与证据保留

首次绑定会一次收集全部问题，并保存已成功绑定的条目。后续模型只能用TaskFactsPatch替换全部未解决fact_id的source_id/quoted_text；不能重写已绑定条目、改变解释和检查项、增删事实或漏掉待修项。结构合法的成功条目保留，不因另一个条目失败而丢失。

修复仍在原事实提取逻辑阶段内有界执行；预算耗尽且来源仍未绑定时明确降级，不能静默删除条件换取complete。`source_bindings.jsonl`保存状态历史，`source_binding_state.json`是最新投影；原始请求、响应和校验错误继续保留。

纯JSON/结构错误发生在事实绑定之前时，按初始schema有界修复；已有绑定会话后只接受patch schema。两种情况都保留原始响应。

### 按声明检查项覆盖

一个来源引句可以支持多个独立check_item，各有全局唯一item_id。C的每条案例必须对应一个check_item_id，并与其fact_id一致。若声明all_declared_items，必须检查所引用事实里的全部已声明检查项，不能只取其中一个作为全部覆盖；抽样只标sampled。

关闭旧issue时还要复查原check-item/input对，不能换成同一事实中的另一个检查项。覆盖记录会显式保存task_exhaustiveness_proven=false：程序不证明模型已提取原题全部条件，也不能从自然语言自动证明每项在语义上原子化。

结果新增source_bindings_complete、declared_check_item_count、pipeline_completed、mechanism_evaluable。pipeline_completed表示生成流程正常执行到了检查阶段，不等于答对或issue全解决；mechanism_evaluable表示至少有一份通过绑定/角色/引用等结构语义检查的审计记录，不等于审计内容在数学上正确。

## 两份真实响应的离线回放

来源为已保存的v1 TaskFacts两份响应。回放工具 `tools/replay_source_bindings.py` 使用显式旧→新schema迁移：丢弃模型填写的旧坐标，保留原始引文；元数据旧路径不会靠删前缀自动修正。task_type和数学任务的null entry_point作为不提取的元数据逐条记录排除原因，原条目保留在迁移凭据中。

| 输入 | 精确绑定 | 仍未绑定 |
|---|---:|---|
| 首次真实响应的10条prompt引文 | 9 | F02漏掉原文的`&`，准确标为unmatched |
| 第二次真实响应的10条prompt引文 | 10 | 无 |
| 用第二份响应的F02引句定向修复首份结果 | 10 | 无；此前成功的9条完全保留 |

F01由程序定位为[6,97)，没有采用模型的[4,152)。同一原文支持F01/F09等不同解释时，两条事实均保留，不按引文去重。

这项回放只检验来源绑定。旧分组事实的原解释保留，并给出带legacy标记的占位检查项以适配回放契约；**没有把旧三个点的组合解释自动证明成三个原子条件，也没有生成新的模型输出**。首份F01的real-coefficient解释仍保留为model_asserted，表明来源绑定不会悄悄修正语义。下一次真实提取是否能正确拆分检查项仍需观察。

完整结果见 `SOURCE_BINDING_REPLAY_20261020.json`，含每条原始定位、迁移说明、原句、程序跨度、状态历史及定向patch。

## 本地验证结果

新增22项有针对性的检查，全套172项测试执行通过。主要通过条件：

1. 模型schema不要求位置或路径；正常JSON解码后的TeX、空格、换行和Unicode精确保留。
2. 重复和重叠引文不自动选择第一处；短引文仍按真实唯一性处理；漏字、改空格和删符号不能自动对齐。
3. 数学元数据来源被排除，代码entry_point可按白名单绑定；未知旧包装层路径不被隐式改写。
4. 同来源的不同解释不被删掉。多个绑定错误一次反馈；成功条目和原解释/检查项在patch期间保留。
5. 漏修、重复ID、修改已锁定条目、用整份事实重写替代patch等情况被拒绝，已成功绑定的数据仍可查看。
6. 一个事实含三个声明检查项时，只检查一项不能标全部覆盖；三个独立案例可通过声明项覆盖检查；日志不声称整题穷尽。
7. 关闭issue必须复查原检查项，不能仅复用其父fact_id和输入。
8. 原反例优先保留、repair/rebuttal和14次逻辑预算继续生效，旧三份初稿缓存可精确复用。
9. CLI帮助正常；未显式live时不会创建输出目录或发送请求。

原140的23个冻结文件SHA256均匹配。本轮不重新评分，原0分及degraded结果保持原记录。测试使用本地脚本化transport，不是外部API调用或模型效果实验。

## 文件与复现

- `src/coreta/task_audit_binding.py`：来源解析、锁定修复、检查项覆盖和运行状态。
- `src/coreta/run_task_audit_binding.py`：独立真实运行入口，默认使用已接入的DeepSeek配置。
- `design/source_binding_prompts.json`、`design/source_binding.schema.json`：新提示和机器契约。
- `tests/test_source_binding.py`：新增22项检查。
- `engineering/SOURCE_BINDING_VALIDATION_20261020.txt`：完整验证输出。
- `engineering/SOURCE_BINDING_IMPLEMENTATION_SUMMARY_20261020.json`：源文件哈希、命令和冻结检查。

在项目目录执行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_source_binding.py -v
.\.venv\Scripts\python.exe tools/replay_source_bindings.py
.\.venv\Scripts\python.exe -m coreta.run_task_audit_binding --help
```

下一步：按v2源文件和提示另行冻结140单次真实工程回归。观察新schema的实际输出可靠性、事实提取粒度、反例发现/保留/处理/复核及最终分数。当前证据限于来源绑定与状态协议的本地行为。

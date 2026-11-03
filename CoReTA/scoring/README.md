# 离线评分入口

评分模块与Agent运行模块分开，执行 `python -m coreta.scoring --help` 查看命令。正式评分在Linux中运行；Windows可通过 `--image <固定镜像ID>` 调用Linux数学容器，原生Windows仅有诊断模式。代码始终在Docker中执行。2026-10-19最终镜像已通过集成检查，见 ../engineering/LINUX_SCORING_READY_20261019.md。

## 数学

gold.json为独立评价端文件，形式为 `[{"task_id":"...","answer":"2"}]`。不传给Agent。先在生成模型输出之前运行：

```bash
python -m coreta.scoring math-preflight --gold gold.json --output preflight.json
```

预核查ready后，结果JSON列表按每条任务的result.json合并，分别保留artifact与prefinal_artifact：

```bash
python -m coreta.scoring math-score --gold gold.json --preflight preflight.json --results results.json --output scores.json
```

预核查与评分模式必须一致，gold改变需重新预核查。固定Math-Verify0.9.0、Linux独立进程主线程；parse/verify内部各5秒，外层进程25秒，评分器异常重试一次。预测无有效表达式记0，评分器异常保留null。多个boxed先提取最后一个平衡表达式，无boxed时按原artifact解析。输出同时含artifact_field，分析前按该字段分开最终与前候选分数，不能混成重复轨迹。

Windows命令追加 `--diagnostic` 仅供适配核查；使用外层限时，关闭库内部不兼容的Windows计时路径。输出有diagnostic_only=true，正式配对分析会拒绝它。

Windows正式数学评分在上述两个命令中均追加 `--image <固定镜像ID>`，不加--diagnostic；预核查与评分必须使用同一镜像。最终镜像ID保存在engineering/SCORING_IMAGE_20261019.txt；开发50题已完成容器预核查，记录在engineering/container-check-20261019-final/development_math_preflight.json。

## HumanEval容器

在CoReTA目录构建镜像（已实际构建并验证；Docker Hub不可达时本机使用AWS托管的Docker官方基础镜像，具体digest见工程记录）：

```bash
docker build -f scoring/Dockerfile -t coreta-scoring:0.3.1 .
docker image inspect --format '{{.Id}}' coreta-scoring:0.3.1
```

保存返回的不可变sha256 image id；正式运行清单记录构建环境与包清单。Dockerfile的基础镜像标签及传递依赖仍需在实际Linux构建时落实，不能把Windows依赖清单当作容器已复现。

samples.jsonl为每题一行 `{"task_id":"HumanEval/0","solution":"完整源码"}`，空答案保留。母数据必须来自正式冻结的HumanEval+ v0.1.10全量数据文件；输入可为jsonl或jsonl.gz，按实际样本精确抽取原记录，不修改测试。每个方法/重复/前后候选分别评分：

```bash
python -m coreta.scoring humaneval --samples samples.jsonl --mother-data HumanEvalPlus.jsonl.gz --job new-score-job --image sha256:实际镜像id
```

启动器禁网、非root、只读根目录和输入，给独立输出和临时缓存，限制CPU/内存/进程数，总限时默认1800秒。job目录必须不存在。实际部署须保证本地Docker守护进程能访问这些挂载路径。

固定EvalPlus0.3.1；样本复制到/output后运行官方evaluate（该版无output_file参数）。子集使用HUMANEVAL_OVERRIDE_PATH；记录母数据与子集指纹、id清单和镜像。全部原/增强测试开启；导入plus_score要求base_status与plus_status都为pass。无Docker时报错，不回退到宿主exec。

## MBPP开发题

评价端record.json为 `task_id, artifact, test_imports, test_list` 四字段，使用冻结训练题的官方值，不能传回Agent：

```bash
python -m coreta.scoring mbpp --record record.json --job new-mbpp-job --image sha256:实际镜像id
```

每题默认容器总限时30秒。测试导入/构造故障记scoring_error，候选语法/执行/断言失败记0。容器整体超时保留评分故障以便定位，不静默当作候选错误。它不是MBPP+正式分数。

## 接口来源

- [Math-Verify官方说明](https://github.com/huggingface/Math-Verify/blob/main/README.md)
- [EvalPlus v0.3.1 evaluate](https://github.com/evalplus/evalplus/blob/v0.3.1/evalplus/evaluate.py)
- [EvalPlus v0.3.1 HumanEval覆盖路径](https://github.com/evalplus/evalplus/blob/v0.3.1/evalplus/data/humaneval.py)

本机Linux数学与代码评分已用官方参考实现、错误/空答案完成验证；尚无真实模型结果。

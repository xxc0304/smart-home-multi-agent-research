# Linux评分环境就绪

日期：2026-10-19。状态：Docker Linux引擎、隔离评分及开发数学gold预核查通过；真实模型联调待完成。

## 本次实际结果

- 完整内核启动时间更新为2026-10-19 09:46:42，HypervisorPresent=True。
- Docker Linux引擎29.8.2就绪，WSL内核6.18.54.1，分配约8GB RAM与12逻辑CPU。环境记录见 DOCKER_ENGINE_READY_20261019.json。
- Docker Hub授权端点连接被重置；改用AWS托管的Docker官方Python镜像。基础镜像固定为 `public.ecr.aws/docker/library/python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1`。
- 最终评分镜像ID见 SCORING_IMAGE_20261019.txt。实际安装库及版本见 requirements.linux-scoring.lock.txt；镜像与包清单均已保存。
- .dockerignore仅允许评分worker和Dockerfile进入构建上下文，没有将本地虚拟环境、安装包、数据或凭据打入镜像。

## 验证证据

最终镜像的7项真实容器检查全部通过，报告 `container-check-20261019-final/report.json`：

1. Linux平台、非root UID65532及实际库版本。
2. 数学等价表达式、错误答案、空答案和最终boxed规则分别得到预期结果。
3. 固定GSM8K开发集50题gold全部可解析，预核查ready=true；报告 `container-check-20261019-final/development_math_preflight.json`。
4. HumanEval/0、HumanEval/1官方参考实现通过原始及增强测试。
5. 同两题空答案均判错。
6. 首道固定MBPP开发题官方参考实现通过官方断言。
7. 同题空答案判错。

所有代码执行均在禁网、非root、只读输入/根目录及资源受限的容器中。上述是工程构造/参考实现核查，不是CoReTA模型效果实验。模型调用为0。

49项本地unittest全部通过，报告 E0_REPORT_LINUX_STAGE_20261019.json。其中新增Math-Verify特殊超时异常和容器外层超时重试回归。Math-Verify的TimeoutException继承BaseException，现已显式捕获，评分失败重试后保留null，不中断整批或假记零分。

## 接口补充

Windows可通过 `coreta.scoring math-preflight/math-score --image <固定镜像ID>` 使用正式Linux评分；不再需要将Windows诊断模式当作替代。镜像与预核查报告须一致。数学批处理在独立Linux容器主线程中运行，并按题记录评分错误；代码评分接口继续使用固定官方EvalPlus0.3.1。

## 下一步

本地协议与评分工程核查通过，可进入DeepSeek单题真实联调。尚需核对实际API响应、输出契约兼容性及输入计数，再完成单题生成→评分→日志的闭环。不要将本报告理解为已跑E1、主结果或B3；正式MATH-500全量gold也尚未做预核查。

镜像来源依据：[AWS官方Docker镜像说明](https://aws.amazon.com/blogs/containers/docker-official-images-now-available-on-amazon-elastic-container-registry-public/)、[AWS官方Python镜像示例](https://aws.amazon.com/blogs/containers/building-better-container-images/)。

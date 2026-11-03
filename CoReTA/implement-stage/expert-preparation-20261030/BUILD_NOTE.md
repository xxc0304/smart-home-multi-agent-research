# Build Note

| Rung | Feature | Acceptance check | Tier | Status |
|---|---|---|---|---|
| F0 | 显式fixture讨论请求到完整smoke轨迹 | `.venv/Scripts/python.exe tools/prepare_expert_discussion.py --smoke` | MUST | PASS exit0 |
| F1 | 真实T分组及SFT导出 | `.venv/Scripts/python.exe tools/prepare_expert_training.py` | MUST | PASS exit0 |
| F2 | 可见性、私密性、失败和无消息检查 | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_expert_preparation.py -v` | MUST | PASS 18 checks exit0 |
| F3 | 官方评分、旧输出回放与累积检查 | `.venv/Scripts/python.exe tools/prepare_expert_discussion.py --verify` | MUST | PASS exit0 |

## Run record

开始前已读取AGENTS、handoff、当前计划、STAGE_REVIEW和已有协议/评分/数据构造。现有工作树保留，不初始化仓库，不提交既有无关修改。

F0首次exit0，24步fixture完整。F1首次exit0，1800/200，248组，七项关联重叠为零。F2首次exit0，17检查。F3初次失败：旧controlled_scoring返回3项却解包4项；改正接口使用后exit0，六项官方评分一致，4份原始旧响应文件逐字核对、重放为24步兼容fixture。参考长度压力10,395token，不是后端实测或上界。

累积检查：`-m unittest discover -s tests -p test_expert*.py -v`，34 checks PASS，exit0。旧局部重放工具未改动。0项目实验模型调用/训练/部署，无live科学结果，H题目与标签文件未读。没有保留函数返回数值的假实现；smoke文件本身为显式fixtures。

本阶段文件列表：tools/expert_discussion.py、tools/expert_discussion_scoring.py、tools/prepare_expert_training.py、tools/prepare_expert_discussion.py、tests/test_expert_preparation.py、本目录文档与smoke、data/expert-training-20261030-v1。因这些文件未在base commit中，审查使用文件列表；未把其他既有修改纳入审查。分阶段commit未执行，以保留现有未提交工作树。

## Deferred

真实模型/训练/部署、实际chat-template token测量、预算冻结及研究结果。身份披露与开放问答投票为显式候选配置；正式启动审核尚未通过。

## Blockers

离线工作无阻塞；实际模型、硬件及计算授权不作为已具备条件。


## Assumption sweep与修订

按实现技能调用新审阅agent（同家族GPT-6-Astra，不能称跨家族独立通过）。首轮JSON存SWEEP_ROUND1.json，发现一处未声明语义：未提供solo时可能启用主比较。已先记录A-011（Source=sweep），修正为团队描述性结果，必须完整一致配对才开放配对比较；补临时文件声明路径回归检查。新旧35项相关检查exit0，完整verify再次exit0；第2轮复核已返回：0未声明语义选择，same-family/provisional，仅实现假设检查，不是跨家族或研究主张认证。无新的数值占位实现，fixtures仍显式标记。

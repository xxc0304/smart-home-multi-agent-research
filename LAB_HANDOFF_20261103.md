# 实验室主机接手（2026-11-03）

用户已获分配 RTX 3090 主机；尚未登录核实显存、系统、CUDA、权限和可用时长，未进行真实训练。

先读：
1. CoReTA/AGENTS.md
2. CoReTA/handoff.md 和 CURRENT_STATE.md 顶部 R29
3. CoReTA/implement-stage/expert-answer-only-20261101/README.md
4. CoReTA/implement-stage/team-controls-20261101/README.md
5. CoReTA/refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md

当前：B0仅答案专家训练与V/C评价入口、B1两轮四分支程序已实现并完成离线CPU检查；真实GPU训练、C专家资格和团队生成尚未进行。先实机预检，再有限B0训练及独立C资格；通过后B1按1–2→8→累计32题接续，32题仅开发。pending配置不代表运行许可，不直接启动大批次。

## 新主机获取

```bash
git clone https://github.com/xxc0304/smart-home-multi-agent-research.git
cd smart-home-multi-agent-research
```

这是私有仓库，使用自己的GitHub登录或SSH密钥。已有副本先确认无本地修改，再git pull --ff-only。

## 迁移边界

本次同步代码、配置、研究记录及交接资料。CoReTA/data/、runs/、虚拟环境、安装器、模型权重不在Git中。不能把克隆成功当作实验可运行。
数据来源和构建记录见CoReTA/dataset.md及research/musique-data-preparation-20261030/；实际运行前须迁移原有冻结数据包并核对manifest/hash，不能重新随机切分。历史运行原件须按需另行迁移；仓库中的报告引用可能指向尚未迁移的runs/文件。

不要上传SSH密码、GitHub令牌或模型服务密钥。3090硬件及后端检查通过后再按现行计划填写运行配置。

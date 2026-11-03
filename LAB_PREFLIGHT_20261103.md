# 2026-11-03 实机迁移阶段

目标：在实验室3090上建立可继续工作的代码、冻结数据和隔离环境；本阶段不训练。

已验证：Tailscale direct、SSH专用密钥登录、Ubuntu24.04/Python3.12.3、RTX3090 24576MiB/驱动560.35.05。项目位于/data2/xiaoxinchen/agent-research，main=eeae977；venv=/data2/xiaoxinchen/venvs/coreta。/data2剩约1.6TB。系统盘仅12GB，不用于模型缓存。

原冻结训练包、训练/验证评分材料、v0.2输入包和MuSiQue来源目录已迁移。归档SHA256=DEB458618248635CEEEE79423C7B97873F8E68D97AD18E03A2D06A534B4B9FCE，远端校验OK。未重新切分。B0 check-data在服务器通过：1796/200，no_C_D_H_bodies_read=true；结果位于CoReTA/runs/lab3090-preflight-20261103/DATA_CHECKS.json。最小项目依赖已安装，Git状态干净（此记录迁移前）。

助手自审PASS仅迁移/数据接口及最小环境。CUDA版torch、transformers/peft/accelerate/bitsandbytes和模型权重尚未安装或验收，CUDA工具链版本不能从nvidia-smi推定；训练/专家资格/团队实验均未启动。下一步按既有B0计划建立GPU依赖及固定模型revision，验证模板/完整长度/显存和技术短步，再冻结预算。不能从本阶段推断专家优势。

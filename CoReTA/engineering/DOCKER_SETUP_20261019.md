# Docker安装与项目推进记录

日期：2026-10-19。状态：软件安装成功，Windows功能待重启生效；尚未运行Linux容器。

## 环境结果

- Windows build26200、约16GB RAM；CPU固件虚拟化与SLAT均为True。
- Docker Desktop4.95.0已以当前用户模式安装，官方Docker Inc数字签名Valid，安装退出码0。位置：`%LOCALAPPDATA%/Programs/DockerDesktop`。
- Docker CLI实测输出：`Docker version 29.8.2, build 7fc2dff`。这仅验证客户端，不表示引擎已就绪。
- WSL3.0.3.0 MSI已安装，微软签名Valid，SHA256与微软发行页一致，安装退出码0。WSL版本检查成功，默认版本2。
- VirtualMachinePlatform已启用，Windows返回RestartNeeded=true。尚未重启，WSL状态仍提示WSL2虚拟化运行条件未生效；重启后再确认，不将安装成功等同于容器可用。
- 本轮没有重启电脑、启动模型请求或运行生成代码。

初次WSL自动下载遭403，改用微软官方GitHub发行MSI；初次Docker安装因缺VirtualMachinePlatform退出1，启用功能后重试安装成功。原始结果见docker-setup-20261019目录的JSON及安装日志。

## 并行完成的项目工作

- 冻结官方源数据：GSM8K train7473、MBPP sanitized train120、MATH-500 test500、HumanEval+ v0.1.10共164题。HF提交、下载URL与实际文件指纹记录在 DEVELOPMENT_DATA_MANIFEST_20261019.json。
- 按预定哈希顺序选择GSM8K/MBPP各50题；MATH-500与HumanEval题面用于规范化去重。公开题面与评价答案/测试分别存于data/development-20261019/public和evaluation。
- 各前3题的工程计划为6任务×3条件=18个团队轨迹，正常调用上限156；各前10题的E1候选计划为20任务×3条件=60个团队轨迹，上限520。这里只生成计划，实际模型调用0。
- 新增coreta.batch：默认计划生成，真实执行需显式--live和--max-jobs；共享初稿银行、输入对应性、任务级恢复、失败尝试保留、无密钥拒绝启动；不按分数补跑。
- 新增测试后实际运行47项unittest，全部通过。报告 E0_REPORT_DOCKER_STAGE_20261019.json；所有响应来自测试构造器。

## 重启后的顺序

1. 用户保存工作并重启Windows，使VirtualMachinePlatform生效；本轮没有安排自动重启。
2. 启动Docker Desktop，确认Linux引擎可用；在新终端检查docker info。当前终端可能尚未刷新安装时更新的PATH。
3. 构建评分镜像并运行可信构造样例的隔离评分烟雾检查；再接入正式Linux数学预核查。
4. 核对DeepSeek接入与实际token计数后，先打通一个真实开发任务及评分，再按工程/试点计划逐步扩大，不一次性提交60个轨迹。

Docker镜像、Linux正式评分、真实模型交互仍未验证。E0保持PARTIAL。

来源：[Docker官方Windows安装说明](https://docs.docker.com/desktop/setup/install/windows-install/)、[微软WSL3.0.3发行页](https://github.com/microsoft/WSL/releases/tag/3.0.3)。

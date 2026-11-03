# 重启后环境检查

2026-10-19 09:44 +0800。Docker Desktop已启动检查，Linux引擎未就绪，未构建镜像或调用模型。

- VirtualMachinePlatform为Enabled，固件虚拟化和SLAT均True。
- HypervisorPresent=False；WSL2仍报告虚拟化运行环境未生效。
- 当前启动项没有显式hypervisorlaunchtype=Off；本轮没有修改启动配置。
- 系统内核启动时间仍为2026-10-18 21:19:44，早于组件启用；最新User32事件为2026-10-19 01:30:12“关闭电源”，未看到此次安装之后的完整内核启动事件。

据此判断：尚未完成使新组件生效的完整内核重启；关机再开机可能由Windows快速启动恢复旧内核。需要用户保存工作后使用开始菜单“重启”，之后再检查；不据此要求修改BIOS或重新安装Docker。

原始证据：docker-setup-20261019/hypervisor-boot-check.json、reboot-evidence.json。微软说明快速启动保留内核，而Restart执行完整启动周期：https://learn.microsoft.com/en-us/troubleshoot/windows-client/setup-upgrade-and-drivers/fast-startup-causes-system-hibernation-shutdown-fail 。

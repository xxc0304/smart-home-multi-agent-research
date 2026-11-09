# 主动停止与保留记录

2026-11-09 P10 STOP：用户明确要求停止这批并保留记录。已核实PID2767473身份后发送SIGINT，进程退出，GPU2MiB/0%。停止前12完整单元+第13部分单元（25完整分支），357返回=305新增+52复用；358attempt中1条正在生成被中断无返回，如实保留，不自动补跑。原运行器捕获KeyboardInterrupt记STOPPED_SYSTEM_FAULT，原状态不覆盖，CANCELLATION.json明确CANCELLED_BY_USER，不是自发技术故障。停止后357响应/12完整评分全请求、历史、种子、token、全员adapter路由审计PASS；原freeze未变。完整run本机归档，5主文件SHA与远端逐字一致。因研究优先级停止，未以质量结果选停止点，不作为完整实验/独立确认。无新生成任务、无自动续跑或替代实验。

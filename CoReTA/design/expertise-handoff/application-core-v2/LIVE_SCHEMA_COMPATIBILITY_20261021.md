# v2最小真实接口兼容检查

2026-10-21，已完成。使用既有官方DeepSeek Responses传输及deepseek-flash配置，实际3次HTTP、零传输重试、零格式恢复、零失败，3份用量记录完整，未知用量尝试0。

| 场景 | 检查内容 | 实际结果 |
|---|---|---|
| 无已有U | 动态schema中的空U集合、新建应用、result=null、missing非空、request非空 | 服务完成；本地schema校验及固定JSON逐字段比较通过 |
| 已有U修订 | target=U1、artifact_uses、artifact=null、missing=null、request=null | 服务完成；校验及复制比较通过 |
| 无请求额度时退役 | request仅允许null、applications为空、retire_applications含U2 | 服务完成；校验及复制比较通过 |

响应model均为deepseek-flash，status均为completed。输入本地估计分别1361、1261、1076 tokens；每请求输出上限1024。请求只要求复制给定公开JSON，数组为物品展示顺序，不是参考排序；没有运行解题提示、求解任务或评分。

## 证据

- 工具：tools/check_application_v2_live_compatibility.py。
- 真实记录：runs/application-v2-live-compatibility-20261021/compatibility.json、requests.jsonl、responses.jsonl。
- 单独工具预检：runs/application-v2-compatibility-offline-20261021/，使用脚本传输并阻止urllib网络；该目录不算真实接口证据。

工具在发送前先本地检查全部固定值和状态动作，最多3次HTTP且首失败即停。未改原运行器、schema、提示、任务、评分或既有结果。

## 能说明什么

新APPLY动态schema在这三种代表性取值下可被当前服务接受，输出可被既有JSON解析器读取并通过schema校验。

这没有检查完整阶段提示、真实长输入、多轮模型协作、资料优势或解题改善，也不能保证未来输出永不出现格式错误。不能将复制成功算作知识接续或专长利用成功。

下一步准备具有可核验资料优势与应用结果的开发任务及内容核验依据，再进行小规模真实模型行为检查。142项离线工程检查与此次3次接口检查属于不同证据。

# 工作板v3工程验证

日期：2026-10-22（Asia/Shanghai）。本次验证程序路径与接口格式，不评价解题能力。

## 结果

| 项目 | 结果 | 范围 |
|---|---|---|
| 新增工作板离线检查 | 18/18通过 | 脚本固定输出，经真实Gateway/schema/运行器；网络被mock并禁止真实访问 |
| 扩展回归 | 184/184通过，0失败/错误/跳过 | 新工作板18项及既有application_ranking、application_v2、handoff检查 |
| 四项任务CLI准备 | 成功，API0 | 学生会长distributed；仅真实INITIAL请求构造与本地输入长度估算 |
| 十五项任务CLI准备 | 成功，API0 | 月球distributed_r0；仅INITIAL，不是整队解题 |
| 固定复制场景本地预检 | 12/12合法 | schema及动作一致性，不依赖服务 |
| DeepSeek真实格式复制 | 12/12通过 | 每次schema合法、动作合法、内容逐字段一致；零重试、零格式恢复 |

新增18项覆盖：三人19/四人29次上限及轮转；初答不见他人稿、同轮不见他人新offer；各成员保留原资料权限；后果检查不先看本次use_record/peer verdict；完整候选可读取；无法应用跳过空检查并返回理由；中断时回退F；全部初答失败；上下文超限在HTTP前停止；收尾预算预留；没有可交付版本不记成功；局部稿不能被收尾reuse；不变产物不记采纳；未入选O与W来源能找到作者；重复来源多摘录；非法引用与动作拒绝；快照复制；未知工具版本拒绝。

## 真实调用记录

第一次受限网络目录`runs/workboard-v3-copy-live-20261022/`：首请求发生URLError，0个有效模型输出，用量未知；按首错停批。它不是格式失败，也不从总调用尝试中删除。

通过授权网络路径执行的目录`runs/workboard-v3-copy-live-20261022-network/`：12次请求，12份用量完整，全部固定内容复制一致。未改变模型、schema或检查场景，未发采样seed。

合计客户端记录13次HTTP尝试：1次网络失败（用量不确定）+12次成功请求。原始请求与响应分别保留；不声称总共只尝试12次。

复制内容使用fixture_a等人工标签，与任务金标准无关。兼容性脚本没有发送方法的完整解题提示；因此只证明所测schema与固定值能在既有接口返回，不证明长上下文、自然贡献、真实推理或后续批次永不发生格式错误。

## 证据文件

- 离线：`runs/workboard-v3-offline-validation-20261022/summary.json`及`unittest.log`
- 真实兼容：`runs/workboard-v3-copy-live-20261022-network/compatibility.json`、`requests.jsonl`、`responses.jsonl`
- 网络失败：`runs/workboard-v3-copy-live-20261022/compatibility.json`
- 准备：`runs/workboard-v3-initial-prepared-20261022/`、`runs/workboard-v3-moon-initial-prepared-20261022/`
- 工具：`tests/test_workboard.py`、`tools/check_workboard_compatibility.py`

所有路径相对CoReTA项目根目录。原始响应中模型自报内容不作为正确性事实。

## 下一阶段

可以准备真实行为试跑的冻结方案；尚不能直接把这些检查当能力实验。

先限定一个已有真实任务，写清实际方法提示、预算、停止条件和过程核验标准，观察正常解题中是否真正发生自主贡献、实际试用及用法/后果核对。公平普通讨论/请求式黑板仍需单独适配并冻结，不能拿当前新方法直接与旧的较少调用基线比较。本轮没有运行该行为试跑或能力对比。

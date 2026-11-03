# W01资产核对与W04起始案例

2026-10-29，用户要求开始核对；只检索、下载公开材料并离线检查，不启动模型实验。

- [ASSET_AVAILABILITY.md](ASSET_AVAILABILITY.md)：主要结论、官方来源、字段、缺项和下一步。
- [CASE_SEED_8.md](CASE_SEED_8.md)：8个案例单位/7道题的人工可读卡片；[完整JSON](CASE_SEED_8.json)含本地实际请求/响应和作者原记录。
- [LOCAL_ASSET_AUDIT.json](LOCAL_ASSET_AUDIT.json)：三批本地170槽位和作者hidden记录字段审计。
- [PBT_ARCHIVE_INSPECTION.json](PBT_ARCHIVE_INSPECTION.json)、[PBT_ARROW_FIELDS.json](PBT_ARROW_FIELDS.json)：真实LFS对象及10主Arrow表读取证据；两模型模板元数据对照。
- [HIDDENBENCH_FULL_PROFILE_AUDIT.json](HIDDENBENCH_FULL_PROFILE_AUDIT.json)：新下载两份全信息结果字段、条件与首条记录。
- [source_snapshots/SOURCE_FETCH_RECORDS.json](source_snapshots/SOURCE_FETCH_RECORDS.json)：官方源码与目录快照链接；只作文本读取，未执行上游代码。

可重复的本地检查：`audit_local_assets.py`检查既有文件，`inspect_pbt_archive.py`检查/缺失时下载公开PBT归档，`inspect_pbt_arrow.py`用pyarrow读取表，`fetch_hiddenbench_full_profile.py`检查/缺失时下载两份官方全信息文件。数据规范位置见data/external下对应README；Arrow库本次位于临时目录，脚本支持`--module-dir`显式指定。新环境安装依赖/访问网络时按环境权限执行，不能把本脚本运行当模型实验结果。

8例为助手目的性初筛，未独立盲标；W01助手核对完成不等于能力专家数据准备完成。下一步W02定义与人工事实核验、W05规范及W06采样规则。

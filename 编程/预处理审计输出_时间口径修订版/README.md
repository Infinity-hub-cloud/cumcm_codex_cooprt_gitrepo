# Q1/Q2 正式预处理输入

状态：`CURRENT`；数据版本：`PREP-TIME-REV-20260911T170805+0800`。

- `audit/`：审计报告、摘要和 manifest。
- `normalized/attachment1_single_day.csv`：固定单日电价/模板轴。
- `normalized/attachment2_actual_long.csv`：真实负载/光伏长表。
- `normalized/attachment3_forecast_long.csv` 与旧 `attachment3_mapped_10min.csv`：保留的原审计产物；不用于 Q3 修订版时间映射。
- `normalized/attachment4_actual_long.csv`：Q4 相关数据；当前未进入问题 4。

注：文件名以磁盘和全量资产清单为准；模型读取前由配置哈希门禁验证。原始附件仍位于 `../../C题/附件/` 且只读。

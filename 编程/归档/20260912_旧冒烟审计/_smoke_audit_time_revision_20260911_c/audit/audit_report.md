# C 题数据预处理与人工审计报告

> 状态：`PASS`（脚本只读运行；未生成模型、预测或求解结果）  
> 生成时间：`2026-09-11T16:44:00+08:00`  
> 输入目录：`D:\Users\LENOVO\Desktop\数学建模\正式比赛C题`  
> 输出目录：`D:\Users\LENOVO\Desktop\数学建模\国赛团队共享工作区\编程\_smoke_audit_time_revision_20260911_c`  

## 1. 人工先看结论

- 错误数：`0`；告警数：`0`。
- 原始附件未被修改；规范化数据全部写入 `normalized/`。
- 时间口径采用人工确认规则：附件 1/2/4 为瞬时时刻，按左端点保持映射到随后 10 分钟；模板标签严格保留。
- 该报告不是模型运行结果；所有异常必须由人工逐项确认、关闭或登记。

## 2. 参数接口快照

| 参数 | 值 |
|---|---|
| interval_count | 144 |
| delta_minutes | 10 |
| hourly_step_minutes | 60 |
| hourly_horizon | 24 |
| start_date | 2025-01-01 |
| end_date | 2025-12-31 |
| output_start_date | 2025-02-01 |
| output_end_date | 2025-12-31 |
| update_times | 0:00, 6:00, 12:00, 18:00 |

## 3. 检查结果

| 检查 | 状态 | 级别 | 详情 |
|---|---|---|---|
| required_path | PASS | error | 附件\附件1.xlsx |
| required_path | PASS | error | 附件\附件2.xlsx |
| required_path | PASS | error | 附件\附件3.xlsx |
| required_path | PASS | error | 附件\附件4.xlsx |
| required_path | PASS | error | 附件\附件5 |
| attachment1_sheet_names | PASS | error | 实际工作表：['Sheet1'] |
| attachment1_dimensions | PASS | error | rows=145, cols=4 |
| attachment1_headers | PASS | error | headers=['时间', '电价', '小区负载', '光伏发电预测功率'] |
| attachment1_time_axis | PASS | error | actual_first_last=[10]...[1440], expected_first_last=(10,)...(1440,) |
| attachment2_sheet_names | PASS | error | 实际工作表：['小区负载', '光伏发电实际功率'] |
| attachment2_load_dimensions | PASS | error | rows=366, cols=145 |
| attachment2_load_time_axis | PASS | error | actual_first_last=[10]...[1440] |
| attachment2_load_date_coverage | PASS | error | count=365, first_last=[datetime.date(2025, 1, 1)]...[datetime.date(2025, 12, 31)] |
| attachment2_load_duplicate_dates | PASS | error | unique=365, rows=365 |
| attachment2_pv_dimensions | PASS | error | rows=366, cols=145 |
| attachment2_pv_time_axis | PASS | error | actual_first_last=[10]...[1440] |
| attachment2_pv_date_coverage | PASS | error | count=365, first_last=[datetime.date(2025, 1, 1)]...[datetime.date(2025, 12, 31)] |
| attachment2_pv_duplicate_dates | PASS | error | unique=365, rows=365 |
| attachment3_sheet_names | PASS | error | 实际工作表：['Sheet1'] |
| attachment3_dimensions | PASS | error | rows=1461, cols=26 |
| attachment3_headers | PASS | error | headers=['日期', '预报时刻', '预报1小时', '预报2小时', '预报3小时', '预报4小时', '预报5小时', '预报6小时', '预报7小时', '预报8小时', '预报9小时', '预报10小时', '预报11小时', '预报12小时', '预报13小时', '预报14小时', '预报15小时', '预报16小时', '预报17小时', '预报18小时', '预报19小时', '预报20小时', '预报21小时', '预报22小时', '预报23小时', '预报24小时'] |
| attachment3_date_coverage | PASS | error | actual_first_last=[datetime.date(2025, 1, 1)]...[datetime.date(2025, 12, 31)], expected_first_last=[datetime.date(2025, 1, 1)]...[datetime.date(2025, 12, 31)] |
| attachment3_record_order | PASS | error | 发布记录未严格按日期和配置发布时间顺序排列 |
| attachment3_daily_update_count | PASS | error | 2025-01-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-01-31 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-02-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-03-31 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-04-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-05-31 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-06-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-07-31 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-08-31 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-09-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-10-31 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-11-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-01 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-02 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-03 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-04 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-05 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-06 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-07 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-08 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-09 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-10 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-11 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-12 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-13 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-14 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-15 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-16 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-17 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-18 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-19 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-20 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-21 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-22 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-23 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-24 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-25 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-26 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-27 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-28 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-29 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-30 更新次数=4 |
| attachment3_daily_update_count | PASS | error | 2025-12-31 更新次数=4 |
| attachment4_sheet_names | PASS | error | 实际工作表：['Sheet1'] |
| attachment4_price_dimensions | PASS | error | rows=366, cols=145 |
| attachment4_price_time_axis | PASS | error | actual_first_last=[10]...[1440] |
| attachment4_price_date_coverage | PASS | error | count=365, first_last=[datetime.date(2025, 1, 1)]...[datetime.date(2025, 12, 31)] |
| attachment4_price_duplicate_dates | PASS | error | unique=365, rows=365 |
| template_file_set | PASS | error | actual=['result1.xlsx', 'result2.xlsx', 'result3.xlsx', 'result4-2.xlsx', 'result4-3.xlsx'], expected=['result1.xlsx', 'result2.xlsx', 'result3.xlsx', 'result4-2.xlsx', 'result4-3.xlsx'] |
| result1.xlsx_sheet_names | PASS | error | 实际工作表：['计划购电量', '充放电量'] |
| result1.xlsx_计划购电量_dimensions | PASS | error | actual=[145, 2], expected=(145, 2) |
| result1.xlsx_计划购电量_interval_labels_parse | PASS | error | first=0:10-0:20, last=0:00+1-0:10+1 |
| result1.xlsx_计划购电量_interval_sequence | PASS | error | actual_first_last=[(10, 20)]...[(1440, 1450)], expected_first_last=[(10, 20)]...[(1440, 1450)] |
| result1.xlsx_充放电量_dimensions | PASS | error | actual=[7, 5], expected=(7, 5) |
| result2.xlsx_sheet_names | PASS | error | 实际工作表：['计划购电量', '充放电量', '紧急购电量'] |
| result2.xlsx_计划购电量_dimensions | PASS | error | actual=[335, 147], expected=(335, 147) |
| result2.xlsx_计划购电量_interval_labels_parse | PASS | error | first=0:10-0:20, last=0:00-0:10+1 |
| result2.xlsx_计划购电量_interval_sequence | PASS | error | actual_first_last=[(10, 20)]...[(1440, 1450)], expected_first_last=[(10, 20)]...[(1440, 1450)] |
| result2.xlsx_计划购电量_date_start | PASS | error | first_date=2025-02-01 |
| result2.xlsx_计划购电量_date_end | PASS | error | last_date=2025-12-31 |
| result2.xlsx_充放电量_dimensions | PASS | error | actual=[20, 6], expected=(20, 6) |
| result2.xlsx_紧急购电量_dimensions | PASS | error | actual=[11, 3], expected=(11, 3) |
| result3.xlsx_sheet_names | PASS | error | 实际工作表：['计划购电量', '调整购电量', '充放电量', '紧急购电量'] |
| result3.xlsx_计划购电量_dimensions | PASS | error | actual=[335, 147], expected=(335, 147) |
| result3.xlsx_计划购电量_interval_labels_parse | PASS | error | first=0:10-0:20, last=0:00-0:10+1 |
| result3.xlsx_计划购电量_interval_sequence | PASS | error | actual_first_last=[(10, 20)]...[(1440, 1450)], expected_first_last=[(10, 20)]...[(1440, 1450)] |
| result3.xlsx_计划购电量_date_start | PASS | error | first_date=2025-02-01 |
| result3.xlsx_计划购电量_date_end | PASS | error | last_date=2025-12-31 |
| result3.xlsx_调整购电量_dimensions | PASS | error | actual=[335, 147], expected=(335, 147) |
| result3.xlsx_调整购电量_interval_labels_parse | PASS | error | first=0:10-0:20, last=0:00-0:10+1 |
| result3.xlsx_调整购电量_interval_sequence | PASS | error | actual_first_last=[(10, 20)]...[(1440, 1450)], expected_first_last=[(10, 20)]...[(1440, 1450)] |
| result3.xlsx_调整购电量_date_start | PASS | error | first_date=2025-02-01 |
| result3.xlsx_调整购电量_date_end | PASS | error | last_date=2025-12-31 |
| result3.xlsx_充放电量_dimensions | PASS | error | actual=[26, 6], expected=(26, 6) |
| result3.xlsx_紧急购电量_dimensions | PASS | error | actual=[11, 3], expected=(11, 3) |
| result4-2.xlsx_sheet_names | PASS | error | 实际工作表：['计划购电量', '充放电量', '紧急购电量'] |
| result4-2.xlsx_计划购电量_dimensions | PASS | error | actual=[335, 147], expected=(335, 147) |
| result4-2.xlsx_计划购电量_interval_labels_parse | PASS | error | first=0:10-0:20, last=0:00-0:10+1 |
| result4-2.xlsx_计划购电量_interval_sequence | PASS | error | actual_first_last=[(10, 20)]...[(1440, 1450)], expected_first_last=[(10, 20)]...[(1440, 1450)] |
| result4-2.xlsx_计划购电量_date_start | PASS | error | first_date=2025-02-01 |
| result4-2.xlsx_计划购电量_date_end | PASS | error | last_date=2025-12-31 |
| result4-2.xlsx_充放电量_dimensions | PASS | error | actual=[20, 6], expected=(20, 6) |
| result4-2.xlsx_紧急购电量_dimensions | PASS | error | actual=[11, 3], expected=(11, 3) |
| result4-3.xlsx_sheet_names | PASS | error | 实际工作表：['计划购电量', '调整购电量', '充放电量', '紧急购电量'] |
| result4-3.xlsx_计划购电量_dimensions | PASS | error | actual=[335, 147], expected=(335, 147) |
| result4-3.xlsx_计划购电量_interval_labels_parse | PASS | error | first=0:10-0:20, last=0:00-0:10+1 |
| result4-3.xlsx_计划购电量_interval_sequence | PASS | error | actual_first_last=[(10, 20)]...[(1440, 1450)], expected_first_last=[(10, 20)]...[(1440, 1450)] |
| result4-3.xlsx_计划购电量_date_start | PASS | error | first_date=2025-02-01 |
| result4-3.xlsx_计划购电量_date_end | PASS | error | last_date=2025-12-31 |
| result4-3.xlsx_调整购电量_dimensions | PASS | error | actual=[335, 147], expected=(335, 147) |
| result4-3.xlsx_调整购电量_interval_labels_parse | PASS | error | first=0:10-0:20, last=0:00-0:10+1 |
| result4-3.xlsx_调整购电量_interval_sequence | PASS | error | actual_first_last=[(10, 20)]...[(1440, 1450)], expected_first_last=[(10, 20)]...[(1440, 1450)] |
| result4-3.xlsx_调整购电量_date_start | PASS | error | first_date=2025-02-01 |
| result4-3.xlsx_调整购电量_date_end | PASS | error | last_date=2025-12-31 |
| result4-3.xlsx_充放电量_dimensions | PASS | error | actual=[26, 6], expected=(26, 6) |
| result4-3.xlsx_紧急购电量_dimensions | PASS | error | actual=[11, 3], expected=(11, 3) |

## 4. 错误与告警

无。

## 5. 工作簿统计

### 附件1.xlsx

```json
{
  "dimensions": [
    145,
    4
  ],
  "price": {
    "count": 144,
    "min": 0.3713,
    "max": 1.3952,
    "mean": 0.7661972222222222
  },
  "load_kw": {
    "count": 144,
    "min": 3309.3934,
    "max": 5958.9696,
    "mean": 4626.0336708333325
  },
  "pv_kw": {
    "count": 144,
    "min": 0.0,
    "max": 7612.316,
    "mean": 2311.7848194444446
  }
}
```

### 附件2.xlsx

```json
{
  "sheets": {
    "小区负载": {
      "dimensions": [
        366,
        145
      ],
      "date_count": 365,
      "values": {
        "count": 52560,
        "min": 1995.7176,
        "max": 7978.8849,
        "mean": 4626.033670125543
      }
    },
    "光伏发电实际功率": {
      "dimensions": [
        366,
        145
      ],
      "date_count": 365,
      "values": {
        "count": 52560,
        "min": 0.0,
        "max": 10216.2,
        "mean": 2311.7857090962652
      }
    }
  },
  "joined_date_count": 365,
  "joined_row_count": 52560
}
```

### 附件3.xlsx

```json
{
  "dimensions": [
    1461,
    26
  ],
  "issue_record_count": 1460,
  "long_forecast_row_count": 35040,
  "mapped_10min_row_count": 210240,
  "configured_issue_minutes": [
    0,
    360,
    720,
    1080
  ]
}
```

### 附件4.xlsx

```json
{
  "sheet": {
    "dimensions": [
      366,
      145
    ],
    "date_count": 365,
    "values": {
      "count": 52560,
      "min": 0.0076,
      "max": 1.7936,
      "mean": 0.7661976046423137
    }
  },
  "negative_price_count": 0,
  "row_count": 52560
}
```

### 附件5_templates

```json
{
  "result1.xlsx": {
    "计划购电量": {
      "dimensions": [
        145,
        2
      ],
      "first_rows": [
        [
          "时间段",
          "购电量"
        ],
        [
          "0:10-0:20",
          null
        ],
        [
          "0:20-0:30",
          null
        ]
      ],
      "nonempty_cells": 146
    },
    "充放电量": {
      "dimensions": [
        7,
        5
      ],
      "first_rows": [
        [
          "时间段",
          "充电量",
          "放电量",
          "时刻",
          "储电量"
        ],
        [
          "0:00-4:00",
          null,
          null,
          "0:00",
          null
        ],
        [
          "4:00-8:00",
          null,
          null,
          "24:00",
          null
        ]
      ],
      "nonempty_cells": 13
    }
  },
  "result2.xlsx": {
    "计划购电量": {
      "dimensions": [
        335,
        147
      ],
      "first_rows": [
        [
          "日期\\时间",
          "0:10-0:20",
          "0:20-0:30",
          "0:30-0:40",
          "0:40-0:50",
          "0:50-1:00",
          "1:00-1:10",
          "1:10-1:20",
          "1:20-1:30",
          "1:30-1:40"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ],
        [
          "2025-02-02 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 481
    },
    "充放电量": {
      "dimensions": [
        20,
        6
      ],
      "first_rows": [
        [
          "日期",
          "时间段",
          "充电量",
          "放电量",
          "时刻",
          "储电量"
        ],
        [
          "2025-02-01 00:00:00",
          "0:00-4:00",
          null,
          null,
          "00:00:00",
          null
        ],
        [
          null,
          "4:00-8:00",
          null,
          null,
          "24:00",
          null
        ]
      ],
      "nonempty_cells": 39
    },
    "紧急购电量": {
      "dimensions": [
        11,
        3
      ],
      "first_rows": [
        [
          "日期",
          "购电时间段",
          "购电量"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null
        ],
        [
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 9
    }
  },
  "result3.xlsx": {
    "计划购电量": {
      "dimensions": [
        335,
        147
      ],
      "first_rows": [
        [
          "日期\\时间",
          "0:10-0:20",
          "0:20-0:30",
          "0:30-0:40",
          "0:40-0:50",
          "0:50-1:00",
          "1:00-1:10",
          "1:10-1:20",
          "1:20-1:30",
          "1:30-1:40"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ],
        [
          "2025-02-02 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 481
    },
    "调整购电量": {
      "dimensions": [
        335,
        147
      ],
      "first_rows": [
        [
          "日期\\时间",
          "0:10-0:20",
          "0:20-0:30",
          "0:30-0:40",
          "0:40-0:50",
          "0:50-1:00",
          "1:00-1:10",
          "1:10-1:20",
          "1:20-1:30",
          "1:30-1:40"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ],
        [
          "2025-02-02 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 481
    },
    "充放电量": {
      "dimensions": [
        26,
        6
      ],
      "first_rows": [
        [
          "日期",
          "时间段",
          "充电量",
          "放电量",
          "时刻",
          "储电量"
        ],
        [
          "2025-02-01 00:00:00",
          "0:00-4:00",
          null,
          null,
          "00:00:00",
          null
        ],
        [
          null,
          "4:00-8:00",
          null,
          null,
          "24:00",
          null
        ]
      ],
      "nonempty_cells": 48
    },
    "紧急购电量": {
      "dimensions": [
        11,
        3
      ],
      "first_rows": [
        [
          "日期",
          "购电时间段",
          "购电量"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null
        ],
        [
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 9
    }
  },
  "result4-2.xlsx": {
    "计划购电量": {
      "dimensions": [
        335,
        147
      ],
      "first_rows": [
        [
          "日期\\时间",
          "0:10-0:20",
          "0:20-0:30",
          "0:30-0:40",
          "0:40-0:50",
          "0:50-1:00",
          "1:00-1:10",
          "1:10-1:20",
          "1:20-1:30",
          "1:30-1:40"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ],
        [
          "2025-02-02 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 481
    },
    "充放电量": {
      "dimensions": [
        20,
        6
      ],
      "first_rows": [
        [
          "日期",
          "时间段",
          "充电量",
          "放电量",
          "时刻",
          "储电量"
        ],
        [
          "2025-02-01 00:00:00",
          "0:00-4:00",
          null,
          null,
          "00:00:00",
          null
        ],
        [
          null,
          "4:00-8:00",
          null,
          null,
          "24:00",
          null
        ]
      ],
      "nonempty_cells": 39
    },
    "紧急购电量": {
      "dimensions": [
        11,
        3
      ],
      "first_rows": [
        [
          "日期",
          "购电时间段",
          "购电量"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null
        ],
        [
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 9
    }
  },
  "result4-3.xlsx": {
    "计划购电量": {
      "dimensions": [
        335,
        147
      ],
      "first_rows": [
        [
          "日期\\时间",
          "0:10-0:20",
          "0:20-0:30",
          "0:30-0:40",
          "0:40-0:50",
          "0:50-1:00",
          "1:00-1:10",
          "1:10-1:20",
          "1:20-1:30",
          "1:30-1:40"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ],
        [
          "2025-02-02 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 481
    },
    "调整购电量": {
      "dimensions": [
        335,
        147
      ],
      "first_rows": [
        [
          "日期\\时间",
          "0:10-0:20",
          "0:20-0:30",
          "0:30-0:40",
          "0:40-0:50",
          "0:50-1:00",
          "1:00-1:10",
          "1:10-1:20",
          "1:20-1:30",
          "1:30-1:40"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ],
        [
          "2025-02-02 00:00:00",
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 481
    },
    "充放电量": {
      "dimensions": [
        26,
        6
      ],
      "first_rows": [
        [
          "日期",
          "时间段",
          "充电量",
          "放电量",
          "时刻",
          "储电量"
        ],
        [
          "2025-02-01 00:00:00",
          "0:00-4:00",
          null,
          null,
          "00:00:00",
          null
        ],
        [
          null,
          "4:00-8:00",
          null,
          null,
          "24:00",
          null
        ]
      ],
      "nonempty_cells": 48
    },
    "紧急购电量": {
      "dimensions": [
        11,
        3
      ],
      "first_rows": [
        [
          "日期",
          "购电时间段",
          "购电量"
        ],
        [
          "2025-02-01 00:00:00",
          null,
          null
        ],
        [
          null,
          null,
          null
        ]
      ],
      "nonempty_cells": 9
    }
  }
}
```

### formula_cells

```json
{
  "附件\\附件1.xlsx": 0,
  "附件\\附件2.xlsx": 0,
  "附件\\附件3.xlsx": 0,
  "附件\\附件4.xlsx": 0,
  "附件\\附件5\\result1.xlsx": 0,
  "附件\\附件5\\result2.xlsx": 0,
  "附件\\附件5\\result3.xlsx": 0,
  "附件\\附件5\\result4-2.xlsx": 0,
  "附件\\附件5\\result4-3.xlsx": 0
}
```

## 6. 文件哈希清单

| 相对路径 | 字节数 | SHA-256 |
|---|---|---|
| C题.pdf | 354389 | 2C098F6AE9DD47AE965AEBDEC3B9FACF3DE6C173F999783C1012C08FC5FB9D2D |
| 理解.md | 16193 | 4A046729D549967BF54DE9BECEF79A6F18FAE29E2C77CC3C3862683524E89035 |
| 附件\附件1.xlsx | 16003 | 66B87134F5ECCCD68184D3539BB1293EF039F9E0FDD955A589B9BFA7F227C377 |
| 附件\附件2.xlsx | 907128 | 2E95FD446BFAFA0D8C59577B5C2E2EA8B3F1DEF20DDE54A3062556F4DA9B4C72 |
| 附件\附件3.xlsx | 293526 | 8A61B06C52BD0D639A1CC37C61A7D9F5B75EDCBCA718F64C1BD3498EC9F9D843 |
| 附件\附件4.xlsx | 409790 | 20E9C93AEAB5E8E21AE4DD15587F9E190F7408692504C1319598461CD654FE71 |
| 附件\附件5\result1.xlsx | 13323 | 28360E0974E7D6065394A8ABA4E14A86773AE0036CC7D3EA1B211B515B03D688 |
| 附件\附件5\result2.xlsx | 18397 | 1C26494CFC6D754E0BD9BFF7E13E1126A73D2D2DA6C5336EB251D89B9A1A1A47 |
| 附件\附件5\result3.xlsx | 265429 | C59DA470CABD0BE23F602C95C8AA9D11EC224A0CDAC216B3E1F218E65D006BDC |
| 附件\附件5\result4-2.xlsx | 18397 | 1C26494CFC6D754E0BD9BFF7E13E1126A73D2D2DA6C5336EB251D89B9A1A1A47 |
| 附件\附件5\result4-3.xlsx | 265429 | C59DA470CABD0BE23F602C95C8AA9D11EC224A0CDAC216B3E1F218E65D006BDC |

## 7. 输出文件

- `normalized/attachment1_single_day.csv`
- `normalized/attachment2_actual_long.csv`
- `normalized/attachment3_forecast_long.csv`
- `normalized/attachment3_mapped_10min.csv`
- `normalized/attachment4_actual_price_long.csv`
- `audit/audit_summary.json`
- 本报告 `audit/audit_report.md`

## 8. 人工复核回传项

1. 确认所有 `ERROR` 是否为真实异常、解析错误或可接受空值。
2. 确认所有 `WARNING` 是否关闭、保留或升级为阻塞项。
3. 抽查附件 1/2/4 的瞬时时刻是否映射到随后 10 分钟，特别是 0:00+1 到次日 0:00-0:10。
4. 抽查附件 3 四个发布时间及跨日映射，并确认五个模板的 144 个时段标签顺序。
5. 回传本报告、`audit_summary.json`、输入文件哈希和人工决定；在此之前不进入模型代码。

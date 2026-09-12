# Q3 人工验收

- 人工验收日期：2026-09-12
- 轨道：`Q3_A3_0ONLY_ZOH`
- 映射：ZOH
- 费用语义：MODEL-B
- 实际运行命令：`python -m q3_baseline.cli --config config/q3_baseline.json run --track Q3_A3_0ONLY_ZOH --output-dir "$q3RevRoot/Q3_A3_0ONLY_ZOH"`
- 环境：Python 3.13.11（Anaconda）；HiGHS 1.15.1
- 输入/代码/配置/数据身份：PASS
- 数值与物理断言：PASS
- 四工作表自动逐值回读：PASS
- Solver evidence：PASS；`solver_updates.csv`与`solver_audit.log`完整，未生成原生HiGHS日志
- WARNING：接受`WARNING-Q3-PLAN-SURPLUS-001`，不得据此声称储能轨迹唯一
- 人工结论：接受为ZOH/00-only对照，不作为Q3主模型。

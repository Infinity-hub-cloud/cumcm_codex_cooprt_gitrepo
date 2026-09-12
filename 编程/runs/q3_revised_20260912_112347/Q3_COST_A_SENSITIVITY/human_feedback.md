# Q3 人工验收

- 人工验收日期：2026-09-12
- 轨道：`Q3_COST_A_SENSITIVITY`
- 映射：INTERP
- 费用语义：MODEL-A
- 实际运行命令：`python -m q3_baseline.cli --config config/q3_baseline.json run --track Q3_COST_A_SENSITIVITY --output-dir "$q3RevRoot/Q3_COST_A_SENSITIVITY"`
- 环境：Python 3.13.11（Anaconda）；HiGHS 1.15.1
- 输入/代码/配置/数据身份：PASS
- 数值与物理断言：PASS
- 四工作表自动逐值回读：PASS
- Solver evidence：PASS；全部更新为预期状态，未生成原生HiGHS日志
- WARNING：接受`WARNING-Q3-PLAN-SURPLUS-001`
- 人工结论：接受为费用语义敏感性；不得与MODEL-B混作主模型或直接机制归因。

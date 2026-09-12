# Q3 人工验收

- 人工验收日期：2026-09-12
- 轨道：`Q3_NOSTORAGE`
- 映射：INTERP
- 费用语义：MODEL-B
- 实际运行命令：`python -m q3_baseline.cli --config config/q3_baseline.json run --track Q3_NOSTORAGE --output-dir "$q3RevRoot/Q3_NOSTORAGE"`
- 环境：Python 3.13.11（Anaconda）；HiGHS 1.15.1
- 输入/代码/配置/数据身份：PASS
- 数值与物理断言：PASS
- 四工作表自动逐值回读：PASS
- Solver evidence：PASS；含364条`OPTIMAL_CLOSED_FORM/ANALYTIC`，其余为预期最优/冷启动状态
- WARNING：接受`WARNING-Q3-PLAN-SURPLUS-001`
- 人工结论：接受为无储能参考，只用于储能价值比较。

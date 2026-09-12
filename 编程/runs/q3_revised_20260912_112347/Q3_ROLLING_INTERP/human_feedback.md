# Q3 人工验收

- 人工验收日期：2026-09-12
- 轨道：`Q3_ROLLING_INTERP`
- 模型版本：`M3-Q3-POINT-MODEL-B-v2.0`
- 映射：INTERP
- 费用语义：MODEL-B
- 实际运行命令：`python -m q3_baseline.cli --config config/q3_baseline.json run --track Q3_ROLLING_INTERP --output-dir "$q3RevRoot/Q3_ROLLING_INTERP"`
- 环境：Python 3.13.11（Anaconda）；HiGHS 1.15.1
- 输入/代码/配置/数据身份：PASS
- 数值与物理断言：PASS
- 四工作表自动逐值回读：PASS
- 候选Excel人工打开抽查：PASS（人工确认）
- MODEL-B费用分账：接受
- Solver evidence：PASS；1条冷启动不求解、1823条HiGHS最优，无失败/不可行；未生成原生HiGHS日志
- 候选SHA-256：`61E81B2E543201B75947FDAE8677A15C3B7E9AFD636043C235C280829AC933FA`
- WARNING：接受`WARNING-Q3-PLAN-SURPLUS-001`、SOC边界命中较多、Git dirty但逐文件哈希齐全、transcript未捕获Python原生输出等限制
- 人工结论：`PASS / ACCEPTED / FROZEN`；冻结为问题三主模型和主结果轨道。
- 提交边界：本验收不等于覆盖官方模板或最终比赛提交批准。

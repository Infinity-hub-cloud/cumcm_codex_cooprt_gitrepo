# Q4-2 价格感知模型

本目录是 `M4-Q4-2-PRICE-AWARE-v0.1` 的 Stage 5 代码入口。完整候选运行包 `../runs/q4_2_20260912_180107/` 已由人工生成，但其状态仍为 `HUMAN_RUN_UNREVIEWED_CANDIDATE`；本目录当前源码与该包的源码/配置身份尚须人工核验或重跑确认。必须显式传入 `--allow-formal-human-run` 才会进入全年候选生成路径。

## 已锁定接口

- `Q4_PRICE_VISIBILITY_RULE=TIMESTAMP_LE_DECISION_VISIBLE`；查询必须满足 `price_timestamp <= decision_time`，否则抛出 `Q4_CAUSAL_PRICE_HARD_FAIL`。
- Attachment4 规范化文件只读使用，标签仍是后续 10 分钟区间左端点；禁止重新预处理。
- 负荷、PV、28 天同刻净负荷残差 q80 缓冲、R0、SOC、互斥和 `qmax=5000/6` 全部继承冻结 Q2。
- 1 月直接读取冻结 Q2 状态链；Feb-1 初始 SOC 固定为冻结 Q2 的 Jan-31 slot144 后状态，不重新优化 1 月。
- P0/P1/P2/P3 参数在正式期前固定；最终排序使用真实 Attachment4 结算成本，预测误差指标只作解释。

## 非求解检查

```powershell
Set-Location -LiteralPath 'F:\2026数模国赛\国赛团队共享工作区\编程'
python -m q4_baseline.cli --config config/q4_baseline.json validate-input
python -m unittest tests.test_q4_price_contracts -v
```

正式运行、反馈文件和失败停止规则见 `../Q4-2_人工运行说明.md`。不得覆盖官方 `../../C题/附件/附件5/result4-2.xlsx`，不得进入 Q4-3；任何现有或新生成的 `result4-2_candidate.xlsx` 都须在人工签认、预测器公平对照和源码身份关闭前标记为候选，不得转录为正式结论。

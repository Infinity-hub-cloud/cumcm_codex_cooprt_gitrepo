# Q3 修订版附件 3 映射

状态：`CURRENT`；映射版本：`Q3-A3-POINT-v1.0`。该目录是 `M3-Q3-POINT-MODEL-B-v2.0` 的当前附件 3 输入，不覆盖旧映射。

| 文件 | 作用 |
|---|---|
| `attachment3_point_forecast_long.csv` | 35040 个 issue/lead 整点功率点 |
| `attachment3_mapped_10min_q3rev_zoh.csv` | 202940 个 ZOH 区间记录 |
| `attachment3_mapped_10min_q3rev_interp.csv` | 202940 个同 issue 插值区间记录 |
| `attachment3_mapping_audit.csv` | 映射核验表 |
| `attachment3_mapping_summary.json` | 行数、边界和 mismatch 摘要 |
| `attachment3_mapping_manifest.json` | 原始/旧/新哈希、时间语义和生成规则 |

时间语义：lead `h` 对应 `issue_datetime + h hours` 的目标整点功率。禁止跨 issue 插值；新 issue 首小时不得倒放 lead1；无合法预测才使用 `fallback_q2_pv`；lead24 只允许最后 10 分钟 endpoint hold。

本目录已经静态/逐行重建验证，但这不等于 Q3 全年 Solver 已运行。下一步由人工按 `../Q3_人工运行说明.md` 执行。

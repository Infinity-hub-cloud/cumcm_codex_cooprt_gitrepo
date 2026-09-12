# 运行证据导航

`runs/` 是不可变证据区。不得覆盖、补写历史 manifest 或把失败目录伪装成成功；新运行必须新建带时间戳目录。

| 目录 | 状态 | 用途 |
|---|---|---|
| `q1_human_run_20260911_204149/` | `PASSED_EVIDENCE` | Q1 人工通过运行包 |
| `q2_human_run_20260911_221035/` | `HISTORICAL` | Q2 早期基线运行 |
| `q2_low_complexity_20260912_001710/` | `HISTORICAL_INCOMPLETE_SUITE` | 首轮实验留痕，不作冻结结论 |
| `q2_low_complexity_20260912_002010/` | `PASSED_EVIDENCE` | 四组完整公平对照；其中 `weekday_buffer/` 为冻结主模型 |
| `q3_20260912_025942/` | `FAILED / OBSOLETE_Q3_SEMANTICS` | 旧语义首轮失败证据 |
| `q3_20260912_031050/` | `FAILED / OBSOLETE_Q3_SEMANTICS` | 旧语义重试失败证据 |
| `q3_20260912_032050/` | `COMPLETED_OLD_RUN / OBSOLETE_Q3_SEMANTICS` | 旧语义曾跑通的四轨道；不得作为当前 Q3 结果 |
| `q3_revised_20260912_112347/` | `ACCEPTED / FROZEN` | Q3修订版完整运行：1个参考目录、7个数值目录、价值分解、8份轨道反馈及统一人工验收 |
| 后续 `q3_revised_<timestamp>/` | 按需 | 只有修复或受控复现时才创建；不得覆盖现有成功包 |

论文手只应从“当前且已人工确认”的运行包提取数值。Q3 的旧运行包用于解释为何重构，不得与 `M3-Q3-POINT-MODEL-B-v2.0` 直接比较或写成修订版结果。

每个有效运行至少核验：`run_manifest.json`、配置快照、指标、断言、Solver 审计、告警/失败日志、候选工作簿、导出回读验证和 `human_feedback.md`。目录摘要不能代替逐文件证据。

# Q2 冻结交付包：weekday_buffer

更新时间：2026-09-12。

- 主模型状态：`ACCEPTED / FROZEN`。
- 模型版本：`M2-Q2-EXPERIMENT-weekday_buffer-v1.0`。
- 技术复核：`PASS`。
- 论文表转录：`PENDING`。
- 比赛提交文件批准：`PENDING_SUBMISSION_APPROVAL`。
- 正式统计期：2025-02-01 至 2025-12-31，共 334 个模板日；1 月只作 SOC/历史预热。

`result2.xlsx` 是成功运行包 `../../runs/q2_low_complexity_20260912_002010/weekday_buffer/result2_candidate.xlsx` 的字节一致复制，SHA-256 为 `CEF7AE5579459E274BBE1387FB22F4A031081CB09AB62D34FF75237E6E8853FC`。官方 `../../../C题/附件/附件5/result2.xlsx` 未被覆盖。

## 论文手入口

1. 阅读 `../../Q2_结果复核与定版建议_20260912.md`，确认指标口径、负面比较和限制。
2. 使用本目录 `论文表1至表3.md` 与三个 `table*.csv`；转录后仍需人工逐表复核。
3. 数值追溯到 `audit_evidence.json`、`provenance.json` 和原运行目录，不能只引用候选 Excel。
4. 查看 `人工验收.md` 区分主模型接受、论文表接受和最终提交批准。

## 文件用途

| 文件 | 用途 | 状态 |
|---|---|---|
| `result2.xlsx` | 已冻结模型的交付候选 | 内容已技术复核；最终提交批准待人工 |
| `论文表1至表3.md` | 四个指定日期的表格汇总 | 待论文手转录/复核 |
| `table1_purchase.csv` | 表 1 购电数据 | 同上 |
| `table2_storage.csv` | 表 2 储能数据 | 同上 |
| `table3_emergency.csv` | 表 3 紧急购电事件 | 同上 |
| `audit_evidence.json` | 独立数值与一致性复核快照 | 技术证据 |
| `provenance.json` | 生成时的来源、哈希和历史状态快照 | 不回写；其中旧 PENDING 是当时状态 |
| `人工验收.md` | 当前人工状态记录 | 主模型已接受，其他门禁分别维护 |

冻结模型使用同星期负载预测、最近同刻光伏预测，以及 28 天同刻净负载残差缓冲（至少 7 样本、正部 0.8 分位数）。不能把缓冲误写成单独负载残差，也不能声称存在独立留出验证或全局最优保证。

若未来确需复现，必须从编程根目录显式使用 `--experiment weekday_buffer` 并写入全新目录；不得覆盖本包或原运行证据。历史压缩快照位于 `../../归档/历史压缩快照/`，不是当前源码来源。

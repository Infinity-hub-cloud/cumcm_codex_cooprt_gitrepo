# Q2候选交付包：weekday_buffer

状态：TECHNICALLY_REVIEWED_PENDING_HUMAN_ACCEPTANCE。费用15212046.69071083元；统计期为2025-02-01至12-31的334个模板日，不含1月预热。

本目录的`result2.xlsx`已填写三张表，是成功人工运行包`../../runs/q2_low_complexity_20260912_002010/weekday_buffer/result2_candidate.xlsx`的原样复制。原始官方模板保持不变。候选、人工接受模型、最终提交批准是三个不同状态。

## 人工需要做什么

1. 阅读[复核报告与补做顺序](../../Q2_结果复核与定版建议_20260912.md)。
2. 若无等效测试记录，按报告第5节执行短补测并保存新日志；不重跑四组。
3. 核对`result2.xlsx`和[论文表1至表3](论文表1至表3.md)，填写[人工验收](人工验收.md)。
4. 模型接受、论文转录和提交批准分别记录；不要改原运行manifest以伪装当时已经验收。

## 文件用途

- `result2.xlsx`：待人工批准的交付候选；计划334天，储能2004条，紧急购电3861条。
- `论文表1至表3.md`及`table1_purchase.csv`、`table2_storage.csv`、`table3_emergency.csv`：题面四个指定日期的数据；没有替队友编辑论文Word。
- `audit_evidence.json`：本次独立数值复核快照（不调用求解器）。
- `provenance.json`：75个来源文件的SHA-256、输入身份、模型选择和验收状态快照。正式运行的完整细节仍在`runs/`，不重复复制大CSV。
- `人工验收.md`：唯一后续人工状态记录，可引用四个仍未回填的历史反馈表。它不属于只读运行指纹快照。

## 不可混淆

`config/q2_baseline.json`及普通CLI默认仍选择baseline；复现推荐模型必须显式传`--experiment weekday_buffer`。保留旧默认是为了可复核，不是推荐继续使用旧结果。

只在人工需要重新求解时使用全新目录：

```powershell
$q2RecheckStamp = Get-Date -Format 'yyyyMMdd_HHmmss'
python -m q2_baseline.cli run --config config/q2_baseline.json --experiment weekday_buffer --output-dir "runs/q2_weekday_buffer_$q2RecheckStamp"
if ($LASTEXITCODE -ne 0) { throw 'Q2 rerun failed' }
```

本次不要求执行上面这段。未来重新运行即产生新证据包，不能直接覆盖当前交付候选；有数值差异先核验代码、求解器、输入和可替代最优解。

候选文件SHA-256：
`CEF7AE5579459E274BBE1387FB22F4A031081CB09AB62D34FF75237E6E8853FC`

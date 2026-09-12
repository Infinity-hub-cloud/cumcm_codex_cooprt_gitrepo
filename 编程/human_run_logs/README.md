# 人工控制台日志导航

本目录保存人工运行的 PowerShell transcript。日志是运行环境和命令的辅助证据，不替代对应 `runs/` 中的 manifest、断言和回读验证。

| 文件前缀 | 对应阶段 | 状态 |
|---|---|---|
| `q1_human_run_*` | Q1 | 已通过运行留痕 |
| `q2_human_run_*` | Q2 | 已完成运行留痕 |
| `q3_20260912_*` | 旧 Q3 | 旧语义调试/运行留痕，不作当前结论 |
| `q3_revised_20260912_112347.console.log` | Q3 修订版 | 完整命令序列和主轨道核验已记录；PowerShell transcript 未收录 Python 原生标准输出 |

禁止编辑旧日志以改变历史。新运行使用 `Start-Transcript -NoClobber` 写入新文件。

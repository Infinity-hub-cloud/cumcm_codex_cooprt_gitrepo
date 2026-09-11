# 论文分区规则

仅当论文手的 Codex 要组织、核对或修改论文材料时读取本文件。

## 项目内受限 Skills

`cumcm-paper-agent-skills/cumcm-paper-agent-skills/.agents/skills/` 中的 4 个 CUMCM 论文 skills 为本目录的项目内受限 skills：仅当工作区位于本“论文”目录、其子目录，或该 skills 包的项目根目录时，才可按当前任务需要发现、读取与调用；不得复制、安装或注册到用户级/其他项目的全局 skills 目录。离开上述范围后，不将其作为可用 skill 使用。

- `cumcm-paper-intelligence`：只读扫描赛题、模型、代码、结果和图表，建立带来源指针的 `.paper/paper_context.md`，标记冲突与证据缺口，不重算或改动科学结论。
- `cumcm-paper-architecture`：依据已确认事实构造论文主线、目录、符号表与必要图表计划；共享数学只定义一次，后续各问突出新增内容与依赖。
- `cumcm-paper-draft`：基于已确认模型、公式、数值和目录撰写 CUMCM 风格正文，优先适配现有 LaTeX/Markdown；证据缺失处保留 `TODO[证据缺口]`，不编造结果。
- `cumcm-paper-audit`：终审任务覆盖、证据可追溯性、结论强度、公式符号、图表承接、重复及模板化表达；仅安全修复文字与结构问题，科学冲突和缺失证据列为阻塞项。

推荐按 `intelligence → architecture → draft → sepia review/refactor → audit` 运行；`math-modeling-paper-pro` 用于科学写作边界，`sepia` 仅在科学事实锁定后进行最小化语言润色。

- 放入：论文草稿、图表、引用记录、排版与终稿检查材料。
- 只使用建模/编程手已明确交接且状态为“已确认”的模型、指标和结果；未确认内容标注待补，不补造数字或结论。
- 不修改 `建模/` 或 `编程/` 的源文件；发现不一致时写出问题和来源路径，交回对应负责人确认。
- 论文、Word/WPS、PDF和提交操作由论文手及人工负责。

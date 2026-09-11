# CUMCM Paper Agent Skills

面向“建模手/编程手已经给出模型、算法和结果，论文手负责理解并成文”的 Codex 工作流。

## 设计目标

- 先理解、后写作；不让写作 agent 偷改科学内容。
- 第一次扫描仓库后生成 `.paper/paper_context.md`，后续优先读取缓存，避免反复吞整个项目。
- 用真实问题依赖构造一条 paper spine，而不是按题号堆四篇小论文。
- 共享数学只定义一次；后续问题只写新增变量、目标、约束、场景与结果。
- 结果、公式、图表和结论可追溯；不把启发式最好结果写成“全局最优”。
- 正文写完后再用 Sepia 做 `review -> refactor`，去模板感但不降低学术语体。

## Skills

1. `cumcm-paper-intelligence`：扫描项目，理解题目、模型、算法、结果、图表与验证，建立论文上下文缓存。
2. `cumcm-paper-architecture`：从真实依赖生成论文主线、目录、符号与图表规划。
3. `cumcm-paper-draft`：按证据写正文初稿，并直接适配现有 LaTeX/Markdown 工程。
4. `cumcm-paper-audit`：检查数字、公式、符号、claim、图表承接、重复与 AI 模板痕迹。

建议同时安装并使用已有的 `math-modeling-paper-pro` 与 `sepia`。前者负责科学写作边界，后者负责专业中文的模板化诊断和最小化改写。

## 安装（项目级）

将本包中的 `.agents/skills/` 复制到比赛项目根目录下的 `.agents/skills/`。`AGENTS.md` 可选，但推荐放在项目根目录，用作长期路由规则。

## 推荐运行顺序

`intelligence -> architecture -> draft -> sepia review/refactor -> audit`

正常情况下不需要在每个 prompt 重复规则；直接使用 `PROMPT.md` 中的短提示词即可。

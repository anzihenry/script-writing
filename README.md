# AI 短剧剧本生产规范

将剧本创作组织成可重复执行、可审核、可交接的生产环节。适用于 AI 真人质感短剧、2D/3D 漫剧，以及已有小说/IP 的短剧改编。

当前版本：1.1，资料核对日期：2026-10-24。本仓库提出的是可调整的内部生产规范，不代表行业统一标准，也不承诺播放量或商业表现。

## 使用入口

采用 **1 个总入口 + 6 个阶段 Skill + 共享规范**。每个阶段均有独立的 SKILL.md、调用描述和界面元数据，明确输入、步骤、交付物与通过条件。

[生产总入口](skills/ai-short-drama-writing/SKILL.md) 用于跨阶段任务或阶段判断。已知当前阶段时直接使用对应技能，不需要重走上游。

| 阶段 | Skill | 主要交付 |
| --- | --- | --- |
| G0 立项 | [ai-short-drama-brief](skills/ai-short-drama-brief/SKILL.md) | 项目简报、约束与假设 |
| G1 设定 | [ai-short-drama-bible](skills/ai-short-drama-bible/SKILL.md) | 总纲、人物弧线、规则与资产表 |
| G2 拆集 | [ai-short-drama-outline](skills/ai-short-drama-outline/SKILL.md) | 分集大纲、伏笔计划 |
| G3 正文 | [ai-short-drama-episode](skills/ai-short-drama-episode/SKILL.md) | 分场剧本、时长预算、连续性更新 |
| G4 审核 | [ai-short-drama-review](skills/ai-short-drama-review/SKILL.md) | 问题报告、按请求修订的稿件及复核 |
| G5 交接 | [ai-short-drama-handoff](skills/ai-short-drama-handoff/SKILL.md) | 台词、场次、资产需求与可选 JSON |

在本项目中可直接请求：

> 请读取 skills/ai-short-drama-writing/SKILL.md 并按其工作。为一部 12 集、每集 90 秒的都市悬疑 AI 漫剧做立项、人物设定和分集大纲。受众为成年观众，主要角色不超过 4 人，常驻场景不超过 3 个。先完成第 1 集样稿和审核，再推进后续批次。

> 请读取 skills/ai-short-drama-review/SKILL.md，审核我提供的第 6 集：检查与前 5 集的连续性、对白时长、伏笔回收和制作可行性。给出定位明确的问题清单，并修订本集及受影响台账。

本仓库保存 Skill 源码，尚未安装到全局技能目录。当前可直接指定对应文件路径使用；安装并被客户端发现后，可用 `$ai-short-drama-brief` 等名称调用。

阶段技能共用 `ai-short-drama-writing/references/` 与 `assets/` 的规范，不复制多套标准。安装整套时保留七个相邻技能目录；仅分发某个阶段时，也需附带 `ai-short-drama-writing` 目录。独立调用不等于脱离共享资料单文件分发。

单阶段请求完成后即止；多阶段请求由总入口连续衔接。只审稿不自动改稿；草稿交接须标明未审核；上游变更须标记受影响的下游产物待复核。

## 规范与模板

| 文件 | 用途 |
| --- | --- |
| [阶段共同约定](skills/ai-short-drama-writing/references/common.md) | 输入、稳定 ID、版本、范围与交付规则 |
| [生产流程](skills/ai-short-drama-writing/references/workflow.md) | 阶段输入输出、职责、审核关口、版本与返工 |
| [写作与审核标准](skills/ai-short-drama-writing/references/standards.md) | 因果、人物、节奏、时长、可制作性、问题等级 |
| [交付物模板](skills/ai-short-drama-writing/assets/templates.md) | 项目简报、设定集、分集表、剧本、台账和交接单 |
| [结构化交接协议](skills/ai-short-drama-writing/references/handoff.md) | ID、字段、状态与 JSON 示例 |
| [完整单集示例](skills/ai-short-drama-writing/references/example.md) | 60 秒原创样例及审核、改写示范 |
| [来源与设计依据](skills/ai-short-drama-writing/references/sources.md) | 已核对的公开资料与本地规范的区别 |

实际项目建议放在 `projects/<项目名>/`，目录按模板生成；没有具体创作任务时不创建空项目。交付终点是供导演、分镜、美术和声音部门使用的剧本包；生成图片、视频及发布由下游另行执行。

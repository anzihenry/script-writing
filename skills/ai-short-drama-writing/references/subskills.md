# 子技能目录与调用边界

共 30 个子技能；加上 6 个阶段入口与 1 个总入口，共 37 个技能。子技能可直接调用；阶段入口按依赖选择需要的步骤，不要求一次执行全部。

文件名中的占位部分由实际项目名、集ID和版本替换。多个子技能可以维护同一文件的不同章节；不为每次调用制造重复正文。


## G0 立项

| 子技能 | 触发任务 | 产物范围 |
| --- | --- | --- |
| [ai-short-drama-intake](../../ai-short-drama-intake/SKILL.md) | 整理创作需求、确认任务范围 | brief.md 的需求与范围 |
| [ai-short-drama-source-map](../../ai-short-drama-source-map/SKILL.md) | 梳理原作材料、来源位置与可改编范围 | brief.md 的素材边界 |
| [ai-short-drama-audience](../../ai-short-drama-audience/SKILL.md) | 定义目标观众、情绪体验和内容定位 | brief.md 的受众定位 |
| [ai-short-drama-premise](../../ai-short-drama-premise/SKILL.md) | 比较故事概念或提炼核心戏剧命题 | brief.md 的概念方案 |
| [ai-short-drama-constraints](../../ai-short-drama-constraints/SKILL.md) | 制定集数时长规格、资产预算或制作边界 | brief.md 的规格与预算 |

## G1 设定

| 子技能 | 触发任务 | 产物范围 |
| --- | --- | --- |
| [ai-short-drama-plot](../../ai-short-drama-plot/SKILL.md) | 设计完整故事总纲、主线因果和结局 | bible.md 的总纲 |
| [ai-short-drama-characters](../../ai-short-drama-characters/SKILL.md) | 创建人物卡、角色口吻与成长弧线 | bible.md 的人物卡 |
| [ai-short-drama-relationships](../../ai-short-drama-relationships/SKILL.md) | 设计人物关系、利益冲突和秘密分布 | bible.md 的关系表 |
| [ai-short-drama-world-rules](../../ai-short-drama-world-rules/SKILL.md) | 设定世界机制、代价限制和故事时间 | bible.md 的规则/时间线 |
| [ai-short-drama-asset-bible](../../ai-short-drama-asset-bible/SKILL.md) | 建立角色地点道具的稳定文字设定与变体 | bible.md 的资产表 |

## G2 拆集

| 子技能 | 触发任务 | 产物范围 |
| --- | --- | --- |
| [ai-short-drama-season-arc](../../ai-short-drama-season-arc/SKILL.md) | 将总纲分配为阶段弧线和集数预算 | outline.md 的全季结构 |
| [ai-short-drama-episode-beats](../../ai-short-drama-episode-beats/SKILL.md) | 把分季结构写成逐集行动与变化 | outline.md 的分集表 |
| [ai-short-drama-hooks](../../ai-short-drama-hooks/SKILL.md) | 设计每集开场、结尾及观众回报 | outline.md 的开场/回报列 |
| [ai-short-drama-foreshadow](../../ai-short-drama-foreshadow/SKILL.md) | 规划线索、误导和揭示时机 | continuity.md 的伏笔计划 |
| [ai-short-drama-episode-bridges](../../ai-short-drama-episode-bridges/SKILL.md) | 检查分集计划的首尾状态和转场 | outline.md 的下集入口及 continuity.md 的计划状态 |

## G3 正文

| 子技能 | 触发任务 | 产物范围 |
| --- | --- | --- |
| [ai-short-drama-scene-plan](../../ai-short-drama-scene-plan/SKILL.md) | 把单集大纲拆成可执行场次 | episodes/<集>-<版本>.md 的分场结构 |
| [ai-short-drama-action-writing](../../ai-short-drama-action-writing/SKILL.md) | 将场次目标或心理描述写成可见行动 | 剧本的动作段 |
| [ai-short-drama-dialogue-writing](../../ai-short-drama-dialogue-writing/SKILL.md) | 撰写或润色人物对白、旁白和画外声 | 剧本的对白段 |
| [ai-short-drama-timing](../../ai-short-drama-timing/SKILL.md) | 估算或调整剧本时长和动作对白并行关系 | 剧本时间预算 |
| [ai-short-drama-continuity-update](../../ai-short-drama-continuity-update/SKILL.md) | 依据已写正文更新实际连续性台账 | continuity.md 的实际记录 |

## G4 审核

| 子技能 | 触发任务 | 产物范围 |
| --- | --- | --- |
| [ai-short-drama-story-audit](../../ai-short-drama-story-audit/SKILL.md) | 诊断剧情因果、人物动机、反转和表达 | reviews/<范围>-<版本>-review.md 的叙事问题 |
| [ai-short-drama-continuity-audit](../../ai-short-drama-continuity-audit/SKILL.md) | 审查已有正文的跨场跨集状态矛盾 | 审核报告的连续性问题 |
| [ai-short-drama-production-audit](../../ai-short-drama-production-audit/SKILL.md) | 检查剧本时长、资产预算及制作风险 | 审核报告的制作问题 |
| [ai-short-drama-revision](../../ai-short-drama-revision/SKILL.md) | 按已定位问题修改剧本及必要关联资料 | 新稿、必要上游/台账更新、changes.md |
| [ai-short-drama-regression-review](../../ai-short-drama-regression-review/SKILL.md) | 复核修订结果及影响范围并汇总审核结论 | 审核报告的复核结论 |

## G5 交接

| 子技能 | 触发任务 | 产物范围 |
| --- | --- | --- |
| [ai-short-drama-delivery-baseline](../../ai-short-drama-delivery-baseline/SKILL.md) | 确定交接版本、依赖和包内文件清单 | handoff/<集>-<版本>.md 的清单 |
| [ai-short-drama-scene-handoff](../../ai-short-drama-scene-handoff/SKILL.md) | 提取场次、首尾状态和必须保留的叙事信息 | 交接单的场次表 |
| [ai-short-drama-audio-handoff](../../ai-short-drama-audio-handoff/SKILL.md) | 提取配音台词、旁白、音效和声音要求 | 交接单的对白/声音表 |
| [ai-short-drama-asset-handoff](../../ai-short-drama-asset-handoff/SKILL.md) | 从指定稿提取角色场景道具和变体制作需求 | 交接单的资产需求表 |
| [ai-short-drama-structured-export](../../ai-short-drama-structured-export/SKILL.md) | 将剧本交接信息导出JSON或校对交付包 | 可选同版本JSON及交付核对结果 |

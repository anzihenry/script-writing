# M4 针对性改进与依赖范围试点

状态：M4验收完成，见 [阶段报告](report.md)。M3已提交7235e0d，M2已提交fbacfea。开发、范围测量、48项保留集及评分/复核全部完成，生产技能未采用候选，未增加索引。

## 已完成

- 单一技能候选：仅在单集入口添加时间锚点、持物动作衔接检查。八次开发运行、两类匿名评分、一项独立争议复核已归档。最终基线3/4、候选4/4；目标S01两组均2/2，差异来自W01现金道具计数，不能归因于目标方法。依据冻结门槛不合入，见 [开发报告](dev/report.md)、[决定](dev/decision.json)。
- 六类依赖范围：每类19个产物的独立语义评阅及逐字证据核验完成。保留文件级权威范围，未实现新索引或主张阅读成本下降，见 [范围报告](scope/report.md)、[决定](scope/decision.json)。
- 工程检查：最终108项完整回归在Python 3.9、3.14及3.15通过，见checks.json和tests-final-*.txt；包含保留集完整性与评分复算。较早检查记录另行保留。当前测试复算旧评阅，不生成新的模型成绩。

## 保留集与历史断点

最终快照位于 holdout/frozen，原M2保留任务12个、两条件各两次共48项。两组规则及配对输入/请求字节相同，见 [预检](holdout/preflight.json)，因此只观察最终质量和重复性，不宣称改动效果。

运行目录 `/tmp/harness-v03-holdout`，48项全部完成并归档 holdout/development；[全量核验](holdout/evidence-check-final.json)确认输入/请求未变、输出哈希一致。[执行历史](holdout/execution-history.json)保留运行、重试及观察时间。六类匿名评阅包已生成，协调者 `/root/m4_holdout_grading` 按类别串行评分，记录在 holdout/blind-review/reviewer-runs.json。下一步完成评分和必要复核，完成M4阶段验收并提交，然后进入M5。

## 中断与限制

开发第5项W01-candidate-r2在旧协调者额度失败时无输出，保留attempt1；用户恢复后fresh attempt2交付，前四项未重跑。首轮recovery评分协调者亦明确额度失败，评阅者恢复时已不在活跃树，具体结束时间未知；无grades交付后fresh评阅完成。记录分别位于dev/development及dev/blind-review/reviewer-runs.json。

执行、评阅均采用指令隔离，宿主技能目录仍可见；匿名输出可能泄露方法。实际模型标识、token、费用未知。自报读取字节不等于实际模型输入，重复固定题目不是独立题材样本。未验证真实制作、配音、接收或外部发布。协议见 [protocol.md](protocol.md)。

2026-11-10恢复：第8项W04-baseline-r1在原协调者额度中断前留下完整answer.md和execution.json，恢复后采集原交付，无重跑；执行者精确完成时间未知，耗时排除，中断记录保存在该run的attempts/interruption-1.json和result.json。前8项全部归档并通过evidence-check-8.json核验，从第9项接续。

2026-11-10第二次恢复：协调者和第20项S04-baseline-r1执行者均明确报告额度失败，但已有完整answer.md和execution.json，恢复后采集原交付，未重跑，排除该项耗时。前20项全部归档并通过evidence-check-20.json核验，从第21项接续。

2026-11-10第三次恢复：第32项W04-candidate-r2未留下输出；旧协调者明确额度失败，执行者恢复时不在活跃树，具体结束时间未知。原attempt1保存在attempts/interruption-1.json，用户明确恢复后启动fresh attempt2，不读取旧尝试。前31项已归档并通过evidence-check-31.json；剩余17项待交付。

2026-11-11恢复：第41项S03-candidate-r2的协调者与执行者均明确额度失败，output为空。原attempt1已保存，用户恢复后fresh attempt2接续。前40项已归档并通过evidence-check-40.json，剩余8项。此前第34项耗时较长，仅进行一次平台阻塞询问，随后正常交付，无重跑，观察记录在progress.json。

2026-11-11评分阶段恢复：第48项在原协调者额度错误前已采集且归档，未重跑；全量48项核验通过，执行历史持久化。新增完整矩阵归档测试通过，六类评分进行中。

2026-11-13结项：48项最终为47项全部必达通过、1项未验证，零已确认关键违规。初评、两类独立复核与字节核验均保留，见holdout/report.md。上述较早断点和“待完成”描述仅记录当时状态，当前以report.md及checks.json为准。

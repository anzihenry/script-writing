# 0.2.0 完整里程碑验收

验收完成日期：2026-10-26。结论：**0.2.0 核心工程实现完成，M1–M5 在已声明的文字预制作与本地单写入者范围内验收通过。**

本轮纠正了最初仅以单测和作者自审宣布完成的不足。依据为事先提交的[补充验收标准](acceptance-plan.md)，并保留原始执行、失败/阻断记录、模型输出、评分和独立裁定。没有真人审稿、真实下游接收或音视频实测；这些不被伪装成通过结果，也不是本版要求补造的证据。

## 里程碑结论与证据

| 里程碑 | 本轮补齐 | 验收结果与证据 |
| --- | --- | --- |
| M1 安全续作 | 独立首次使用复跑，仅依据 README/操作手册，无实现或测试知识 | 旧例追加两集、检查点后修改上游定位 STALE、全新项目完整登记和打包均成功；无阻断文档缺口。[复跑报告](new-user-replay.md)、[实际命令](new-user-commands.json) |
| M2 多集一致性 | 新题材输入与独立 oracle 固定后，两个互不共享结果的执行上下文实际运行审核/状态提取技能 | 每轮预置重大问题3/3检出、正常对照0/3重大误报、必需事实21/21有据提取、预设禁止推断0违反。[评分汇总](grading/summary.md)、[第一轮](runs/round-1/execution.md)、[第二轮](runs/round-2/execution.md) |
| M3 准确返工 | 取消角色对完整登记页的先验知识，真正重写EP002四句对白和五个动作块；更新上游、台账、报告与交接，实际执行模拟反馈闭环 | 三份旧包与三份替代包、23份旧文件保留且哈希核验；独立评审无未解决P0/P1。[请求](revision/request.md)、[变更](revision/project/changes.md)、[独立审查](revision-independent-review.md)。impact另提供真实旧新稿差异、变更行和候选引用：[实际输出](revision/impact-details-current.json) |
| M4 可核对交付 | init模板支持可读Markdown场次/对白表，直接提取核对，无需内嵌JSON；保留JSON兼容 | 正常文本/JSON互通；漏句、错角色、旧源版本、重复或孤立对白、歧义双来源不会MATCH；不支持格式UNVERIFIED。独立首次使用者以纯Markdown完成parity与bundle，覆盖拒绝覆盖旧包的实测操作 |
| M5 验证发布 | 官方Skill校验、全套回归、旧例兼容、完整三集实质返工、独立执行和证据完整性检查 | 52项标准库测试通过；37/37官方Skill校验通过；旧例与当前例结构检查通过。[最终检查](final-checks.json)、[官方结果](official-skill-validation.json) |

## 不是只刷新版本号

旧EP002依赖林夏记得“三号、第四行”，新前提使该路径失效。返工改为林夏不透露纸片出处，来访者主动索取“登记簿里剩下的”，林夏据此追问。她的新结论仅是对方主动提及登记簿，来源与身份仍待核查，没有重新偷偷赋予编号先验。EP001与EP003场内内容复核后可保持，仍更新依赖；它们没有被机械要求重写。

实际失效检查和P1未关闭时的全季审核都返回了阻断结果；修订、复核和问题解决后才生成新包。作者自审与独立评审分别保存。[执行日志](revision/terminal.log)、[差异](revision/content.diff)、[中断恢复核验](revision/resume-audit.md)可回查。演练脚本属于当次操作留痕，不要在已完成副本重复运行并覆盖历史包。

## 语义评测的范围与额外发现

输入由另一个执行者编写，未复用旧“归还”错误样例；oracle 在 ff5b959 提交固定，未提供给两轮技能执行者。父执行者逐项对照原文与oracle评分，事实下标和原始输出哈希随评分保存。所有评测与裁定均为AI执行，不是真人判断或不同模型族比较。

第二轮额外发现 F02 的交样期限信息缺口，第一轮没有报告。独立裁定认为该P1有据，但不能断言人物必然迟到。此项未加入原固定分母，也未删除或当作无效噪声：[额外发现裁定](grading/additional-finding-adjudication.md)。因此“3/3”只指预置问题，不能宣称原文所有潜在问题零漏检，更不能推断任意剧本的生产准确率。

## 保留项与边界

- 独立返工审查发现P2：EP002相邻动作块重复看门，可能拖慢节奏；已留在独立报告，作为后续分镜优化建议，不改写冻结的历史演练产物。
- 三集配音/样片时长、撕口辨识和手部动作仍未实测；预算检查通过不等于成片通过。
- 可读Markdown只支持文档定义的模板约定，不承诺任意旧排版。JSON或可读表只能有一个权威对白来源；动作语义仍需审查。
- impact 的场次/对象是实际引用支持的候选定位，不能代替语义判断或自动豁免文件级复核；没有完整旧稿时不编造差异。
- 继续采用本地单写入者。反馈、接收和测量是有证据的登记；演练的接收明确标为模拟。
- 初轮作者自审记录保留于[历史记录](../0.2.0-review.md)，其“未做独立评测/官方校验缺依赖”等描述是当时时点，不代表当前状态。

## 复验

仓库根运行：

```bash
python3 -m unittest discover -s tests -v
python3 skills/ai-short-drama-writing/scripts/pipeline.py check examples/return-demo
python3 skills/ai-short-drama-writing/scripts/pipeline.py check examples/return-season
python3 skills/ai-short-drama-writing/scripts/pipeline.py check docs/validation/v0.2.0-final/revision/project
python3 skills/ai-short-drama-writing/scripts/pipeline.py impact docs/validation/v0.2.0-final/revision/project --id bible
```

自动测试重新核验旧文件、ZIP成员及来源哈希、当前依赖、真实对白变更、评分与原始输出的绑定。它不重新调用模型，也不把评分JSON的存在当成新的语义评审。重新进行语义试验应使用独立执行上下文，只提供各fixture的request/source与技能，不提供oracle及既有输出，再对照固定答案评分。

官方校验当次使用临时PYTHONPATH中的PyYAML 6.0.3，没有增加管线运行依赖；校验器路径和每个Skill的实际退出码保存在官方结果中。原始diff上下文空白及终端/模型输出末尾空行按原样保存，不为格式清理改变已核验的原始证据。

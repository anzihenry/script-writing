# 多集结构化记录

仅在需要索引或确定性核对时采用。结构化块是所属产物的一部分，改动后须登记新版本。每种标签每文件最多一个块，不从任意旧 Markdown 猜测数据。连续性缺块返回 UNVERIFIED，不代表故事有错；对白核对还支持下面的可读 Markdown 表。

## 连续性

在 continuity 文件记录以下块，location 与 quote 必须能回查同版本正文。before=null 表示此前未知；每个 field 是可比较的离散状态，例如 knows_page、holder。观众使用独立对象 AUDIENCE，不与角色知识混写。闪回使用 temporal=flashback，只进入历史，不覆盖当前状态。

```continuity-json
{"states":[{"object":"PROP001","field":"holder","before":null,"after":"CHAR001","location":"EP001-SC001","quote":"钥匙在林夏右手","temporal":"current"}],"foreshadows":[{"id":"F001","status":"planted","location":"EP001-SC001","quote":"纸片撕口与登记簿吻合"}]}
```

字段和引用通过，只能证明证据存在，不能证明提取语义正确。不要为让 before 一致而修改正文事实。出现冲突交审核处理；取消伏笔使用 cancelled 并给 reason；paid 必须有已投放记录。

## 伏笔计划

outline 文件中的计划与实际记录分开。plant/payoff 是已纳入项目的集 ID，计划改动会使下游失效。样稿阶段只登记本次实际纳入范围的计划，未纳入集数的远期构想保留在文字中。

```outline-json
{"foreshadows":[{"id":"F001","plant":"EP001","payoff":"EP002"}]}
```

运行 `pipeline.py index PROJECT --through EP002 --object PROP001` 查询状态历史；不传 object 则返回所有对象。索引按需构建，缺覆盖或过期时为 UNVERIFIED，冲突/到期漏收为 CONFLICT。RECORDED 表示结构与记录可用，不是语义审核通过。未写到回收集不能按漏收处理。

## 正文与交接核对

选择 JSON 格式时，script-json 是正文的权威场次/对白/资产引用清单；对白原文只在此维护，动作、入出场状态、时间块仍用可读文字。不要复制一份不同的散文台词再期待工具判断哪份为准。handoff-json 是从该清单提取的交接记录，额外必填 source_revision。每份文档每种标签只放一个块。

```script-json
{"scenes":[{"id":"EP001-SC001","location_id":"LOC001","character_ids":["CHAR001"],"prop_ids":[],"dialogue":[{"id":"EP001-D001","speaker_id":"CHAR001","text":"谁？"}]}]}
```

将相同 scenes 提取到 handoff-json，顶层增加 `"source_revision":"v1.0"`。运行 `parity PROJECT --scope EP001`。MATCH 仅覆盖场次顺序、地点、角色/道具引用、对白 ID/顺序/说话者/原文。仅归一化 CRLF 换行；不忽略删词、标点或空格。已登记 export 也参与比较。动作语义、表演和散文一致性仍需审稿。

既不采用下述可读表、又缺少必要 JSON 块的旧格式返回 UNVERIFIED；显式不一致返回 MISMATCH 并阻止 bundle。旧格式可打预制作包，但包内明确保留未验证结论，不冒称已逐句核对。


## 可读 Markdown 模板（无需 JSON）

init 生成的正文和交接模板现在采用此格式。文档包含一次 `<!-- drama-table:v1 -->`，每场用 `## 场次 EP001-SC001` 标题，地点/人物/道具各一行。人物与道具用英文逗号分隔；无道具写 `-`。每场只放一张权威对白表，包括没有对白的场次（保留表头与分隔行）。交接额外必须有 `正文来源版本：v1.0`，填写实际源稿版本。

```markdown
<!-- drama-table:v1 -->
正文来源版本：v1.0

## 场次 EP001-SC001
地点：LOC001
人物：CHAR001, CHAR002
道具：PROP001

| 对白ID | 说话者 | 原文 |
| --- | --- | --- |
| EP001-D001 | CHAR001 | 谁？ |
| EP001-D002 | CHAR002 | 是我。 |
```

场次动作、时长和对白方式可放在其他段落或表格中，引用对白 ID。原文只维护一份。表格分隔符周围空格属于排版，原文内部空格、标点及字词严格比较；原文的竖线写成 `\|`。需要保留首尾空格或多行原文时用 JSON 格式。不能同时提供此标记与 script-json/handoff-json；工具会拒绝歧义来源。

parity 可以比较 Markdown→Markdown、Markdown→JSON 或 JSON→Markdown，已登记导出也参与核对。不带格式标记的任意散文仍为 UNVERIFIED；带标记却缺表头、元数据或含重复 ID 属输入错误，不会报告 MATCH。可读模板支持范围是明确约定，不承诺解析任意历史排版。

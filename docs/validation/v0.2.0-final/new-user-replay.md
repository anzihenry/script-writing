# 0.2.0 首次使用者独立复跑

日期：2026-10-25。结论：本次三个指定流程均能仅依文档完成，没有遇到必须读取实现才能解决的参数或格式卡点。结论仅覆盖最小文字预制作工作流，不等于独立质量批准、实际计时或制作锁定。

## 阅读边界与隔离

只阅读 README、其链接的 operations.md 和 structured-records.md，以及 init 实际生成的 Markdown 模板。未读 pipeline.py 源码、tests、docs/validation 其他验收结果；未依赖已有测试的辅助函数。未调用外部服务。没有额外使用 Skill。

临时根目录：`/tmp/script-writing-new-user-3NVCgh`，以 `mktemp -d /tmp/script-writing-new-user-XXXXXX` 新建。
Python `shutil.copytree` 将 `examples/return-demo` 复制到 `legacy/`，将 `examples/return-season` 复制到 `season/`，未改原示例。只向仓库写本报告及同名 JSON，不提交 Git。

实际 CLI 的完整参数、返回码、stdout、stderr 保存在临时 `commands.json`。模板填写脚本在临时 `fill.py`；填写后文件和 ZIP 都保留，可核查。以下列出全部实际 CLI 命令，长检查点输出仅摘录关键字段。

## 旧例追加与恢复

`episodes --through 3` 返回 `{"added": ["EP002", "EP003"]}`；这是追加生产范围及模板，没有假装新集已完成。
`next --scope EP003 --json` 返回 NEEDS_WORK，首先建议 EP002 / G3 / ai-short-drama-episode，原因同时列 `missing output: continuity/EP002` 和 `missing output: script/EP002`；输入列 bible、outline、continuity_EP001，正确从前置集继续。

## 三集例检查点和故意破坏

保存 NEWUSER-B001，范围为 EP001、EP002、EP003。随后仅在临时 season/brief.md 末尾添加：

> 复跑实验：上游简报增加未经登记的约束：只允许日景。

恢复结果为 NEEDS_WORK，next 是 project / G0 / ai-short-drama-brief，明确原因 `brief: file changed since registration (STALE)`。artifact_errors 同时给出 bible、outline 及三集正文等下游的 `dependency unusable`；changed_since_checkpoint 列出 brief 及 18 个受影响产物。检查点还保留 next_entry 和 reread。可定位根因到 brief，而不只是笼统报告失败。

## 从空项目到 Markdown 交付

init 创建 fresh，项目 NEW-USER-ONE，1 集。用其生成的正文和交接 Markdown 场次表直接填写，保留 `<!-- drama-table:v1 -->`；将地点/人物/道具占位值换成 LOC001、CHAR001/CHAR002、PROP001，写三句真实对白，并填写时间块与动作。

原创最小单集《最后一盏灯》：店员准备关灯，见失主赶来后停手，将柜台钥匙交还；失主道谢离开后关灯。30 秒为 5+6+8+6+5 的估算，2 人、1 场、1 道具。brief/bible/outline/continuity/review/handoff 都写入对应真实内容。作者自审报告明确是创作者本人自审，覆盖实际已读内容；时长未实测、钥匙交接未样片验证、交接在报告时尚未生成，随后在交接单记录实际提取与逐句核对。不假称独立审稿或修后复核。

按 operations 中顺序登记 brief→bible→outline→script→continuity→review→正文 reviewed 元数据→handoff。正文内容不变，按文档保持 v1.0。未写 script-json/handoff-json，也未创建任何交接 export JSON。

check 返回 STRUCTURE_OK；G5 返回 STRUCTURE_READY；parity 返回 MATCH，script/handoff 均为 markdown-table-v1。覆盖场次顺序、地点、人物/道具引用、对白顺序/ID/说话者/原文；动作语义、表演、非结构化散文仍明确 unverified。

第一次 bundle 返回 `BUNDLED: 7 artifacts; not sent to recipient`。ZIP 含交付清单及七个已登记 Markdown 产物。再次用另一个 delivery-id 写同一路径，返回码 2，错误 `bundle destination exists; refusing overwrite`；前后 SHA-256 相同，且 deliveries 仍只有一次成功交付。旧包没有被覆盖。

## 遇到的问题与适用范围

没有遇到阻断本次流程的文档缺口，也没有通过猜测源码规则绕过校验。预计内的失败仅是故意触发的旧包覆盖拒绝；恢复里的 STALE 是故意修改上游的正确结果。

非阻断可读性观察：next 的检查点输出包含全量快照，三集例输出很长；关键信息仍能直接定位。初始化模板较长，有些指导段落可留作工作提示；本次关键表及实质内容已填写。连续性使用可读文字，未尝试结构化 index，因此不对 index 覆盖作成功结论。

## 全部实际 CLI 命令与关键输出

### 1. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py episodes /tmp/script-writing-new-user-3NVCgh/legacy --through 3
```

```text
{"added": ["EP002", "EP003"]}
```

### 2. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py next /tmp/script-writing-new-user-3NVCgh/legacy --scope EP003 --json
```

```text
{
  "status": "NEEDS_WORK",
  "next": {
    "stage": "G3",
    "scope": "EP002",
    "reasons": [
      "missing output: continuity/EP002",
      "missing output: script/EP002"
    ],
    "skill": "ai-short-drama-episode",
    "inputs": [
      {
        "kind": "bible",
        "scope": "project",
        "id": "bible"
      },
      {
        "kind": "outline",
        "scope": "project",
        "id": "outline"
      },
      {
        "kind": "continuity",
        "scope": "EP001",
        "id": "continuity_EP001"
      },
      {
        "kind": "script",
        "scope": "EP002",
        "id": null
      }
    ]
  },
  "changed_since_checkpoint": []
}
```

### 3. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py checkpoint /tmp/script-writing-new-user-3NVCgh/season --id NEWUSER-B001 --scopes EP001 EP002 EP003 --next-entry '恢复 EP003 交接' --reread '简报与三集正文'
```

```text
已保存 NEWUSER-B001；包含全部产物 snapshots、open_issues、next_entry 与 reread。
```

### 4. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py next /tmp/script-writing-new-user-3NVCgh/season --scope EP003 --json
```

```text
{
  "status": "NEEDS_WORK",
  "next": {
    "stage": "G0",
    "scope": "project",
    "reasons": [
      "brief: file changed since registration (STALE)"
    ],
    "skill": "ai-short-drama-brief",
    "inputs": []
  },
  "changed_since_checkpoint": [
    "brief",
    "bible",
    "outline",
    "script_EP001",
    "continuity_EP001",
    "review_EP001",
    "handoff_EP001",
    "export_EP001",
    "script_EP002",
    "continuity_EP002",
    "review_EP002",
    "handoff_EP002",
    "export_EP002",
    "script_EP003",
    "continuity_EP003",
    "review_EP003",
    "handoff_EP003",
    "export_EP003",
    "season_review"
  ]
}
```

### 5. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py init /tmp/script-writing-new-user-3NVCgh/fresh --id NEW-USER-ONE --episodes 1
```

```text
INITIALIZED: blank templates only; no stage passed
```

### 6. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id brief --kind brief --path brief.md --revision v1.0
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 7. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id bible --kind bible --path bible.md --revision v1.0
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 8. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id outline --kind outline --path outline.md --revision v1.0
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 9. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id script_EP001 --kind script --path episodes/EP001-v1.0.md --revision v1.0 --scope EP001
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 10. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id continuity_EP001 --kind continuity --path continuity/EP001-v1.0.md --revision v1.0 --scope EP001
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 11. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id review_EP001 --kind review --path reviews/EP001-v1.0.md --revision v1.0 --scope EP001 --status reviewed --evidence '作者自审；reviews/EP001-v1.0.md 全文，文字预制作通过；未实测、未锁定。'
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 12. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id script_EP001 --kind script --path episodes/EP001-v1.0.md --revision v1.0 --scope EP001 --status reviewed --evidence '作者自审；reviews/EP001-v1.0.md 全文，文字预制作通过；未实测、未锁定。'
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 13. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py register /tmp/script-writing-new-user-3NVCgh/fresh --id handoff_EP001 --kind handoff --path handoff/EP001-v1.0.md --revision v1.0 --scope EP001
```

```text
REGISTERED: metadata recorded; creative quality not inferred
```

### 14. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py check /tmp/script-writing-new-user-3NVCgh/fresh
```

```text
STRUCTURE_OK: registered artifacts consistent; use gate for completeness
```

### 15. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py gate /tmp/script-writing-new-user-3NVCgh/fresh --stage G5 --scope EP001
```

```text
STRUCTURE_READY: perform/document the human quality gate; no status auto-promotion
```

### 16. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py parity /tmp/script-writing-new-user-3NVCgh/fresh --scope EP001
```

```text
{
  "status": "MATCH",
  "reasons": [],
  "formats": {
    "script": "markdown-table-v1",
    "handoff": "markdown-table-v1"
  },
  "coverage": [
    "scene order",
    "scene locations",
    "character/prop references",
    "dialogue order/IDs",
    "speaker",
    "exact text"
  ],
  "unverified": [
    "action semantics",
    "performance",
    "unstructured prose consistency"
  ],
  "source": {
    "id": "script_EP001",
    "revision": "v1.0",
    "sha256": "b77bba0b6e5eeea4e4e45b2bc9e1275f8cab9074a53362f2821c05c3ea58da48"
  }
}
```

### 17. 返回码 0

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py bundle /tmp/script-writing-new-user-3NVCgh/fresh --scope EP001 --output /tmp/script-writing-new-user-3NVCgh/fresh-EP001-v1.0.zip --delivery-id NEWUSER-PKG001
```

```text
BUNDLED: 7 artifacts; not sent to recipient
```

### 18. 返回码 2

```bash
python3 /Users/xiejinheng/Coding/script-writing/skills/ai-short-drama-writing/scripts/pipeline.py bundle /tmp/script-writing-new-user-3NVCgh/fresh --scope EP001 --output /tmp/script-writing-new-user-3NVCgh/fresh-EP001-v1.0.zip --delivery-id NEWUSER-PKG002
```

```text
ERROR: bundle destination exists; refusing overwrite
```

ZIP 前后 SHA-256：`c04ba9cff17bf776ac0c72c1e18664dbfcd62c4852cfff8c19183859d8919493`。

## 可复现的实际填写内容

以下是此次成功登记并打包的七份原始 Markdown 全文；新环境先 init，再用对应内容替换文件并执行上文登记命令。临时路径可替换为新的绝对路径。未登记的 decisions/changes/feedback 仍为 init 模板，不参与交付。

### brief.md

````markdown
# 项目简报


## 需求与范围
原创单集《最后一盏灯》，本次交付文字预制作包。规格为本次文档试跑的作者假设，不是客户确认。
## 素材与改编边界
无外部素材；本次独立创作。
## 受众与叙事承诺
成年通勤观众；承诺用一次等待带来善意回报。
## 概念选择
关店店员发现门口有人奔来，选择延迟关灯；迟到者拿回遗失的钥匙。
## 规格与制作预算
1 集，30 秒估算，中文，AI 真人质感，竖屏 9:16，无片头尾；2 成人角色，1 店内场景，2 套固定服装，1 把钥匙，无特殊场面。
## 未决项与进入 G1 的条件
实际朗读与钥匙细节生成效果由声音及美术验证；不阻碍文字样稿。

````

### bible.md

````markdown
# 故事设定集


## 因果主线与结局
店员准备关门，见失主奔来，选择等待。失主取回钥匙，店员终于关灯。
## 人物卡
CHAR001 小林：店员，想按时下班，愿为别人多等片刻；白衬衫、短发、平静语气。知道钥匙被遗忘但不知道失主是否回来。
CHAR002 阿青：成年顾客，想取回钥匙；蓝夹克、短发、急促语气。知道自己遗失钥匙，不知道店员是否留存。
## 关系与秘密
普通店员与顾客，没有秘密与超自然能力。
## 世界规则与故事时间
现实都市，关门前最后半分钟，顺叙；两人无伤势。
## 资产设定
LOC001 便利店柜台：玻璃门与墙面灯开关，夜内景。
PROP001 单把银色钥匙：开场在柜台，结尾由阿青右手持有；细节需美术验证。
## 改编映射与变更影响
原创，不适用。

````

### outline.md

````markdown
# 全季与分集规划


## 全季阶段弧线
单集闭合：急于离开→选择等候→完成交还。
## 单集事件与回报
EP001：小林手在开关旁→见阿青到门口→收手并递钥匙→阿青拿回钥匙道谢→小林关灯。30 秒，2 人 1 场 1 道具。
## 伏笔计划
无跨集伏笔；钥匙开场可见，同集交还。
## 跨集计划状态
单集试跑，无下集。

````

### episodes/EP001-v1.0.md

````markdown
<!-- drama-table:v1 -->
# 单集分场剧本

项目：NEW-USER-ONE｜范围：EP001｜正文版本：v1.0

> 工作模板。填写真实内容后移除此文件首行标记；删除标记本身不代表审核通过。
> 流程状态、依赖快照和审核依据登记在 project.json；本文提供内容与证据。

目标：交还钥匙。来源 outline.md EP001，30 秒，片头尾为零；按动作块估算，未实测。

## 场次 EP001-SC001
地点：LOC001
人物：CHAR001, CHAR002
道具：PROP001

| 对白ID | 说话者 | 原文 |
| --- | --- | --- |
| EP001-D001 | CHAR002 | 等一下，我的钥匙！ |
| EP001-D002 | CHAR001 | 给你留着呢。 |
| EP001-D003 | CHAR002 | 谢谢你等我。 |

夜内景；小林白衬衫，阿青蓝夹克。入场钥匙在柜台，小林想关灯离店。
| 时间块ID | 秒数/估算区间 | 可见动作 | 对白ID引用/方式 | 声音/屏幕文字 | 并行/串行关系 |
| --- | --- | --- | --- | --- | --- |
| T001 | 5 | 小林手伸向开关，阿青出现在玻璃门外 | 无 | 街道远声 | 串行 |
| T002 | 6 | 阿青推门，小林停手 | EP001-D001 现场急促 | 门铃 | 对白与动作并行 |
| T003 | 8 | 小林从柜台拿起钥匙递给阿青，阿青右手接住 | EP001-D002 现场平静 | 钥匙轻响 | 对白与动作并行 |
| T004 | 6 | 阿青举起钥匙道谢，退到门外 | EP001-D003 现场放松 | 脚步声 | 对白与动作并行 |
| T005 | 5 | 小林微笑，关灯 | 无 | 开关声 | 串行 |
出场钥匙由阿青持有。先见来人再停手；不提前关灯。钥匙交接可拆成手部特写，尚未制作验证。

## 本集计时与连续性摘要

单场合计 30 秒；短句在动作块内并行。结尾阿青持钥匙，双方知道交还完成。无下集、无未收伏笔。未进行实际朗读。

## 未决项与检查

已人工核对三句对白、角色知情和持物变化；尚未朗读或制作样片。

## 可选机器记录

本模板使用 drama-table:v1 可读表直接核对，不需 JSON。格式见技能套件 references/structured-records.md。如改用 script-json，移除此格式标记及权威对白表，避免两套来源；改动后登记新版本。

````

### continuity/EP001-v1.0.md

````markdown
# 实际连续性记录


## 来源
正文 episodes/EP001-v1.0.md v1.0，计划 outline.md v1.0。
## 对象状态
PROP001 在 SC001 T001 柜台→T003 小林拾起递出→阿青右手接住；末尾由阿青带走。
CHAR001 T001 欲关灯→T002 看到来人停手→T005 完成交还关灯。
CHAR002 入场不知钥匙是否被保管→D002 得知保管→T003 接回。
AUDIENCE 开场看见钥匙；T003 看见交还。两人衣着、地点和无伤状态保持。
## 伏笔实际情况
无跨集伏笔。
## 批次交棒
单集结束，无后集入口；若续写须回读 SC001 T003 持物事实。

````

### reviews/EP001-v1.0.md

````markdown
# 审核与复核报告


## 审核范围与依据
2026-10-25，由本次创作者进行作者自审；不是独立审稿。已读 brief、bible、outline、episodes/EP001-v1.0.md、continuity/EP001-v1.0.md 的全部 v1.0 内容。
## 维度结论
叙事：停手等待带来交还结果，SC001 T002→T003 因果清晰。
人物：小林放弃立即离店，动作体现善意；阿青 D001/D003 从焦急转为放松。
连续性：钥匙由柜台经小林交给阿青，符合台账；角色知识只来源于可见动作和 D002。
时长：5+6+8+6+5=30 秒估算；对白短句与动作并行。未朗读，真实时长未验证。
可制作性：2 人 1 场 1 道具，无特殊效果；钥匙手部交接尚未样片验证。
交接完整性：审核时尚未生成交接，待提取后另行逐句核对。
## 问题与复核
未发现阻断文字预制作的 P0/P1。时长和钥匙细节属于待验证项；没有修订，不声称修后复核。
## 最终结论
作者自审通过文字预制作范围；未实测、未制作锁定、未取得外部批准。

````

### handoff/EP001-v1.0.md

````markdown
<!-- drama-table:v1 -->
# 制作交接单

项目：NEW-USER-ONE｜范围：EP001｜正文版本：v1.0

> 工作模板。填写真实内容后移除此文件首行标记；删除标记本身不代表审核通过。
> 流程状态、依赖快照和审核依据登记在 project.json；本文提供内容与证据。

## 基线与用途

正文 episodes/EP001-v1.0.md v1.0，设定 bible.md v1.0，台账 continuity/EP001-v1.0.md v1.0；作者自审通过文字预制作范围，详见 reviews/EP001-v1.0.md。未锁定。

## 文件清单

| 文件/资产 | 来源版本 | 用途 | 已有/缺失/待更新 | 缺失影响 |
| --- | --- | --- | --- | --- |

## 场次与导演约束

| 场ID | 时间/地点 | 人物/道具/变体 | 入场→出场状态 | 必须表达的信息 | 揭示顺序/禁提前曝光 | 风险与替代 |
| --- | --- | --- | --- | --- | --- | --- |

## 对白与声音

正文来源版本：v1.0

## 场次 EP001-SC001
地点：LOC001
人物：CHAR001, CHAR002
道具：PROP001

| 对白ID | 说话者 | 原文 |
| --- | --- | --- |
| EP001-D001 | CHAR002 | 等一下，我的钥匙！ |
| EP001-D002 | CHAR001 | 给你留着呢。 |
| EP001-D003 | CHAR002 | 谢谢你等我。 |

D001 急促、D002 平静、D003 放松；均现场对白，按正文时间块预算，未实测。

| 声音/文字ID或位置 | 音效/环境声/屏幕文字 | 内容 | 作用 | 出现时机/阅读预算 |
| --- | --- | --- | --- | --- |

## 美术资产需求

| 资产ID | 实际出现场次 | 不变锚点 | 变体/首尾状态 | 已有引用 | 需制作/待验证 |
| --- | --- | --- | --- | --- | --- |

## 计时、未决项与验收

目标与估算/实测、跨集连接、待验证事项、责任视角；格式/引用/版本/逐句核对结果。
需要机器读取才另导出 JSON。不得在提取台词或导出时改正文。

## 下游接收与反馈

接收人/日期/版本/意见仅在确有反馈后填写；返工反馈登记 feedback.md，不预填“已接收”。

## 可选机器记录

本模板使用 drama-table:v1 可读表直接核对，正文来源版本必须填写实际版本。格式见技能套件 references/structured-records.md。改用 handoff-json 时移除此标记和权威对白表；不可混用。

## 实际交接补充
正文、设定、台账及作者自审报告全部随包；角色与环境图、配音、样片尚未生成。
场次 SC001 是夜内景；必须先让小林看见阿青再停手，钥匙最后在阿青右手。
美术：LOC001 便利店玻璃门与柜台；CHAR001 白衬衫，CHAR002 蓝夹克，PROP001 单把银色钥匙，全部待制作。
声音：T002 门铃、T003 钥匙轻响、T004 脚步、T005 开关声；无屏幕文字。
时长按 5+6+8+6+5=30 秒估算，未实测。逐句人工核对三句对白与来源，未改写；机器核对另见 parity。
下游接收：尚未收到接收反馈。
````

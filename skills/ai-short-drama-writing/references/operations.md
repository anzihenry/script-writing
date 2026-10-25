# 操作手册与项目数据协议 v1

所有命令从仓库根运行。`pipeline.py` 只使用 Python 3.9+ 标准库，不需要 PyYAML、API 密钥或模型服务。项目路径可改为绝对路径，工具只允许登记项目内文件；不发送产物。

## 命令

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py init projects/my-drama --id MY-DRAMA --episodes 3
python3 skills/ai-short-drama-writing/scripts/pipeline.py status projects/my-drama
```

初始化拒绝覆盖已有目录，只生成待填写模板。`--episodes` 是本次纳入连续生产的集数，不应在缺少用户规格时冒充用户已确认；试运行可以显式选择 1 集样稿。

实际写完对应文件并移除 `<!-- TEMPLATE:UNFILLED -->` 后，依次登记：

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id brief --kind brief --path brief.md --revision v1.0
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id bible --kind bible --path bible.md --revision v1.0
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id outline --kind outline --path outline.md --revision v1.0
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id script_EP001 --kind script --scope EP001 --path episodes/EP001-v1.0.md --revision v1.0
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id continuity_EP001 --kind continuity --scope EP001 --path continuity/EP001-v1.0.md --revision v1.0
```

审核后，先登记报告，再依据真实报告登记正文审核状态。以下 `--evidence` 内容必须替换为实际审稿方式、范围、报告位置与结论；命令不会替你审稿。

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id review_EP001 --kind review --scope EP001 --path reviews/EP001-v1.0.md --revision v1.0 --status reviewed --evidence '实际审稿方式、范围与报告依据'
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id script_EP001 --kind script --scope EP001 --path episodes/EP001-v1.0.md --revision v1.0 --status reviewed --evidence '实际审核报告及结论位置'
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id handoff_EP001 --kind handoff --scope EP001 --path handoff/EP001-v1.0.md --revision v1.0
```

状态元数据变更、内容不变时可以保持正文修订号；它不改变正文哈希。改内容或刷新依赖必须换修订号。锁定稿即便修改元数据也需新路径、新版本，保留原制作基线。

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py check projects/my-drama
python3 skills/ai-short-drama-writing/scripts/pipeline.py gate projects/my-drama --stage G3 --scope EP001
python3 skills/ai-short-drama-writing/scripts/pipeline.py gate projects/my-drama --stage G5 --scope EP001
python3 skills/ai-short-drama-writing/scripts/pipeline.py bundle projects/my-drama --scope EP001 --output /tmp/my-drama-EP001-v1.0.zip
```

`check` 只检查已登记的产物，空注册表可以结构有效；`gate` 才检查阶段缺失。`status` 列各范围的关口，不改变状态。`bundle` 要求 G5 结构就绪并拒绝覆盖现有包，收集依赖闭包和交付清单；未锁定包的用途是预制作。包内不含生成视频或自动接收确认。

## 结构化导出

JSON 由交接 Skill 按[交接协议](handoff.md)生成，工具不从自由文本猜剧情。仅需要机器读取时增加：

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py validate-handoff projects/my-drama/handoff/EP001-v1.0.json
python3 skills/ai-short-drama-writing/scripts/pipeline.py register projects/my-drama --id export_EP001 --kind export --scope EP001 --path handoff/EP001-v1.0.json --revision v1.0
```

打包会检查已登记导出的字段、引用、时长、项目/集ID、正文路径/修订号、设定版本和正文状态。自由文本正文与 JSON 的逐句语义一致性仍由交接审查负责，不能因为结构检查通过就声称已逐句核对。

## project.json 字段

此协议由脚本显式验证，不冒充通用 JSON Schema 解释器。扩展字段可保留，核心字段如下。

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| schema_version | string | `1.0` |
| project_id | string | 非空项目标识 |
| episodes | string[] | `EP001` 等唯一ID，数组顺序定义前后集依赖 |
| artifacts | object | 键为稳定产物ID，每种 kind/scope 只注册一个当前版本 |
| issues | object[] | 问题的唯一机器状态来源，见下表 |
| history | object[] | 工具追加的登记事件与前后快照，不手动删除来掩盖变更 |

产物条目：

| 字段 | 规则 |
| --- | --- |
| kind | brief / bible / outline / script / continuity / review / handoff / export |
| scope | 前三类是 project，其余是已登记集ID |
| path | 项目内的相对路径；拒绝越界路径与指向外部的符号链接 |
| revision | 非空修订号；内容或依赖改变时必须更新 |
| status | draft / reviewed / locked / superseded |
| sha256 | 工具计算的文件哈希，不手动刷新来隐藏修改 |
| depends_on | 自动记录上游 `id / revision / sha256`，不只记录可变文件名 |
| evidence | reviewed/locked 时必填实际依据，工具无法验证真实性 |

默认依赖按[生产管线](pipeline.md)中的矩阵计算，v1 命令不支持自定义生产图。外部素材位置和其他创作依据记录于 brief.md / decisions.md。不要手工添加会被后续登记覆盖的额外依赖，也不要删除必需依赖；特殊生产顺序先调整契约与验证器。

## 问题登记

在 project.json 的 issues 中维护；审核报告按同一 ID 写详细证据。示例字段如下，内容须来自真实检查：

```json
{
  "id": "Q001",
  "scope": "EP001",
  "severity": "P1",
  "status": "open",
  "location": "EP001-SC001 / EP001-D002",
  "summary": "角色说出了尚未获知的信息",
  "affects": ["script_EP001"],
  "evidence": null,
  "verified_revisions": {}
}
```

`affects` 引用已登记产物；状态为 open/resolved/accepted。resolved 或 accepted 必须给出证据，以及所有受影响产物的当前版本，如 `{"script_EP001":"v1.1"}`。P0 不允许 accepted。其后若相关版本再变，先将问题重新打开，再完成修订与复核，不能把旧接受依据沿用到新稿。

项目范围的未解决 P0/P1 阻断所有范围；单集问题影响本集或消费其产物的下游。P2 不阻断结构关口，但仍交给接收方知悉。

## 修订与恢复

1. 记录 changes.md 和必要问题，重新打开受影响的已关闭问题。
2. 写新稿；锁定文件保留原路径内容，不使用原文件覆盖。登记上游新版本。
3. 运行 check/status，读取报告中标出的过期依赖。按顺序修订或复核下游后，使用新修订号登记；依赖变化需要 `--note '实际复核的范围和结果'`。
4. 完成复核再更新问题状态与 verified_revisions。重新提取交接表/JSON，生成新包。

工具不是版本备份系统。history 保留登记快照，锁定文件必须自行保留并纳入 Git。CLI 单写入者串行使用；不支持多人同时修改注册表。

## 返回值与验证

- 0：命令成功；结构就绪不等于创意批准。
- 1：check/gate 发现缺失、过期或未解决问题。
- 2：参数、数据格式、文件读取或写入错误。

运行仓库测试：`python3 -m unittest discover -s tests -v`。不调用外部服务，不生成付费资产。

## 0.2.0 项目续作与问题操作

新增操作兼容原 schema_version 1.0；管理记录使用可选扩展字段。继续单写入者串行运行。

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py episodes projects/my-drama --through 3
python3 skills/ai-short-drama-writing/scripts/pipeline.py issue projects/my-drama add --id Q001 --scope EP001 --severity P1 --location EP001-SC001 --summary '实际发现的问题' --affects script_EP001
python3 skills/ai-short-drama-writing/scripts/pipeline.py issue projects/my-drama list
python3 skills/ai-short-drama-writing/scripts/pipeline.py issue projects/my-drama resolve --id Q001 --evidence '实际复核报告与结论'
python3 skills/ai-short-drama-writing/scripts/pipeline.py issue projects/my-drama reopen --id Q001
```

`episodes --through` 是目标总集数，只追加，重复执行无变更；现有目标文件冲突时整批拒绝。`issue accept` 另外需要 `--actor`，不得接受 P0。修订影响已关闭问题时先 reopen，再登记新版、实际复核后 resolve。问题事件保存在 events 中，原 issues 仍是当前状态来源。

### 恢复与批次检查点

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py next projects/my-drama --scope EP003 --json
python3 skills/ai-short-drama-writing/scripts/pipeline.py checkpoint projects/my-drama --id B001 --scopes EP001 EP002 --next-entry '从 EP003 分场开始' --reread 'EP002 末尾及未回收伏笔'
```

`next` 只读，按项目阶段及前置集顺序列出原因、所需输入和建议技能；不自动执行创作。检查点保存当时的快照与交棒提示，不代表通过；恢复结果会列出此后变化/失效的产物。重复检查点 ID 拒绝，保存新批次时使用新 ID。STRUCTURE_READY 仍不代表质量获批。

### 返工影响与反馈

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py impact projects/my-drama --id script_EP001
python3 skills/ai-short-drama-writing/scripts/pipeline.py impact-note projects/my-drama --source script_EP001 --target script_EP002 --decision reviewed_unchanged --evidence '实际复核范围与结果'
python3 skills/ai-short-drama-writing/scripts/pipeline.py feedback projects/my-drama add --id FB001 --package-id PKG001 --source '接收方' --location EP001-SC001 --evidence '实际观察' --layer script --issues Q001
python3 skills/ai-short-drama-writing/scripts/pipeline.py feedback projects/my-drama update --id FB001 --status awaiting_verification
```

impact 按依赖顺序列直接/间接影响，不声称已经理解情节差异。impact-note 的 rewrite/reviewed_unchanged/pending 绑定当前快照，不能清除文件失效；真实复核后仍需 register 新修订。非锁定稿建议使用新文件路径保存历史；只有快照不能恢复旧正文。

feedback 的 layer 为 script/production/unknown；状态为 triage/in_progress/awaiting_verification/closed。未知包只能停留 triage。关闭需 `--verification` 实际回验证据且关联问题已处理；剧本反馈必须关联问题。记录保存在 project.json，feedback.md 可作阅读说明，不维护另一套状态。生成包或修改剧本不会自动关闭反馈。

### 交付核对、接收与实测

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py parity projects/my-drama --scope EP001
python3 skills/ai-short-drama-writing/scripts/pipeline.py bundle projects/my-drama --scope EP001 --output /tmp/EP001-new.zip --delivery-id PKG002 --supersedes PKG001
python3 skills/ai-short-drama-writing/scripts/pipeline.py receipt projects/my-drama --id PKG002 --status accepted --evidence '实际接收方确认依据'
python3 skills/ai-short-drama-writing/scripts/pipeline.py measure projects/my-drama --id T001 --package-id PKG002 --seconds 63.2 --source '实际配音文件或样片位置' --evidence '实际测量口径与方法'
```

核对格式见[结构化记录](structured-records.md)。每次 bundle 保存交付 ID、文件快照、ZIP 哈希和核对结果，默认状态 pending。未指定 ID 时自动生成；supersedes 必须引用同集已存在包。拒绝覆盖原 ZIP，保存登记失败时删除本次新包。包不发送，接收不自动填写。

receipt 的 pending/accepted/returned 只记录实际接收情况，与正文 locked 分开。measure 不生成音频，数值由实际测量者提供；绑定包内正文版本，已登记导出存在时返回与包内时间预算的偏差，无预算时为 null。模拟数据必须明确标模拟，不代表实测。

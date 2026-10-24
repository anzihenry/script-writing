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

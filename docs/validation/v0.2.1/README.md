# 0.2.1 本地验收记录

日期：2026-10-30。状态：M0–M5 的实现、配置、隔离评测、本地及远端验证完成，发布版本 0.2.1。M5 的语义判断与确定性测试分别报告。

执行环境为 macOS arm64。本报告记录 AI 实现者的自动验证，不是真人审稿或实际下游接收。

## M4 阶段结果（保留原快照）

| 验证 | 结果 | 证据 |
| --- | --- | --- |
| Python 3.9.6 | 74 项测试通过，无跳过或预期失败 | [日志](tests-python39.txt) |
| Python 3.14.10 | 74 项测试通过，无跳过或预期失败 | [日志](tests-python314.txt) |
| Python 3.15.2 | 74 项测试通过，无跳过或预期失败 | [日志](tests-python315.txt) |
| 新旧示例 CLI 回放 | 14 次命令退出码符合预期；旧例 index/parity 保持 UNVERIFIED | [回放](examples.json) |
| 3/30/100 集规模检查 | next/status 均为一次 inspect；15/123/403 个产物分别仅计算同等次数哈希 | [测量](benchmark.json) |
| 真实三集例性能 | next 从 13 次 inspect / 247 次 sha 降至 1 / 19 | test_reliability 中硬性断言 |
| 历史资料保护 | 原 v0.2.0 的旧稿、六个 ZIP 及其哈希完整性测试通过 | test_milestone_evidence |

规模夹具不含 export/season_review，共 3+4N 个产物，区别于包含 19 个产物的真实三集示例。耗时仅表示本机观察，不设 CI 毫秒门槛。测试曾并行运行于三个 Python 进程，日志耗时不可直接作为性能对比。

## M5 完成后的最终验证

| 验证 | 结果 | 证据 |
| --- | --- | --- |
| Python 3.9.6 | 78 项测试通过，无跳过或预期失败 | [最终日志](tests-final-python39.txt) |
| Python 3.14.10 | 78 项测试通过，无跳过或预期失败 | [最终日志](tests-final-python314.txt) |
| Python 3.15.2 | 78 项测试通过，无跳过或预期失败 | [最终日志](tests-final-python315.txt) |
| 两轮隔离语义评测 | 每轮 6/6 预置重大问题检出、六例正常对照无重大误报、12/12 事实问答完整有据 | [语义汇总](semantic/summary.md) |
| 原文引用 | 第一轮 54/54、第二轮 62/62 均匹配原文位置 | 各轮 structure-check.json |
| 归档保护 | 冻结材料、原始输出及评分绑定哈希，并检查案例顺序、引用和计数一致性 | test_semantic_protocol |

最终新增的四项协议测试验证材料隔离与归档完整性，不代替语义审读。两轮使用用户授权的串行独立上下文子代理；评分由父 AI 执行者对照冻结 oracle 完成，没有真人或独立评分者。未出现需要额外裁定的发现；usage limit 中断在产生结果前发生，不算额外评测或择优重跑。

## 已完成的兼容调整

- 连续性引用从“全文子串存在”收紧为完整场次/对白 ID 与对应内容范围绑定。注释、代码示例、其他场次内容不能充当证据。旧散文无法定位时明确未验证，不自动改稿。
- 新增 verify-package，只读比对已登记完整 ZIP 哈希；receipt 的 integrity 为可选字段，接收状态与核验观察分开。损坏包拒绝 accepted，但仍能登记 returned；包缺失允许登记有依据的外部接收并标记 UNVERIFIED。
- next/status 共享命令内检查，查找表、历史分组和哈希缓存均在该次调用结束后丢弃；后续调用重新核验。bundle 保留独立检查步骤，本轮未引入跨命令缓存。
- 旧项目和交接 schema_version 仍为 1.0。既有 52 项测试全部保留，M4 新增 22 项边界/规模测试，M5 再增加四项评测协议与归档测试；连续性测试夹具从无定位散文升级为受支持 JSON，不改历史验收文件。

## CI 与复现

[工作流](../../../.github/workflows/tests.yml)配置 Ubuntu 24.04 Python 3.9、Ubuntu latest Python 3.15 和 macOS latest Python 3.15，push/PR 时运行测试、规模测量和示例回放。使用只读仓库权限，关闭 checkout 凭据持久化，不依赖项目密钥或模型服务。Actions 用法核对自 [checkout](https://github.com/actions/checkout) 与 [setup-python](https://github.com/actions/setup-python) 官方文档。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/benchmark_pipeline.py
python3 scripts/validate_examples.py
```

发布时已推送并完成[远端 CI](https://github.com/anzihenry/script-writing/actions/runs/41063920064)，提交为 `0a2dccd76dac6228ee43992759109231366eecdd`；三个矩阵任务均通过 78 项测试、规模测量及示例回放。[运行与任务证据](remote-ci.json)保留原始结果。后续发布记录提交仅更新文档，并在创建版本标签前再次确认其 CI。

[首次运行](https://github.com/anzihenry/script-writing/actions/runs/41063067427)中 Python 3.9 安装失败，原因是 ubuntu-latest 已指向 Ubuntu 26.04，而官方未提供该平台的 Python 3.9 构建；两个 Python 3.15 任务通过。修复为官方构建清单支持的 Ubuntu 24.04 后全部通过，没有删除最低 Python 版本的验证。

本地三个 Python 版本也均已实际执行。既有测试验证 37 个 Skill 的名称、元数据文件及本地链接；本轮未重新执行官方 Skill 验证器，不将这些检查称为官方复验。

## 保留边界

1. 版本号和 CHANGELOG 已更新；发布沿用 GitHub Release 及自动生成的源码包，不另外生成制作资产。
2. M5 已完成的结果只覆盖冻结的六集短文本案例；完整制作级长剧、未见保留集与真人审稿仍未验证，不能将样本得分外推为通用准确率。
3. 定位正确不能证明提取语义正确；哈希匹配不能证明接收依据真实；没有真实配音、样片或真人审核。

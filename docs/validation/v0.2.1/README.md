# 0.2.1 本地验收记录

日期：2026-10-30。状态：M0–M4 的实现、配置及本地验证完成；远端 CI 尚未运行，未发布 0.2.1。VERSION 保持 0.2.0。M5 的隔离语义评测单独推进，不计入本报告的确定性通过结论。

执行环境为 macOS arm64。本报告记录 AI 实现者的自动验证，不是真人审稿或实际下游接收。

## 结果

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

## 已完成的兼容调整

- 连续性引用从“全文子串存在”收紧为完整场次/对白 ID 与对应内容范围绑定。注释、代码示例、其他场次内容不能充当证据。旧散文无法定位时明确未验证，不自动改稿。
- 新增 verify-package，只读比对已登记完整 ZIP 哈希；receipt 的 integrity 为可选字段，接收状态与核验观察分开。损坏包拒绝 accepted，但仍能登记 returned；包缺失允许登记有依据的外部接收并标记 UNVERIFIED。
- next/status 共享命令内检查，查找表、历史分组和哈希缓存均在该次调用结束后丢弃；后续调用重新核验。bundle 保留独立检查步骤，本轮未引入跨命令缓存。
- 旧项目和交接 schema_version 仍为 1.0。既有 52 项测试全部保留，新增 22 项测试覆盖边界和规模行为；测试夹具从无定位散文升级为受支持 JSON，不改历史验收文件。

## CI 与复现

[工作流](../../../.github/workflows/tests.yml)配置 Linux Python 3.9 / 3.15 和 macOS Python 3.15，push/PR 时运行测试、规模测量和示例回放。使用只读仓库权限，关闭 checkout 凭据持久化，不依赖项目密钥或模型服务。Actions 用法核对自 [checkout](https://github.com/actions/checkout) 与 [setup-python](https://github.com/actions/setup-python) 官方文档。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/benchmark_pipeline.py
python3 scripts/validate_examples.py
```

本轮没有推送提交，因此不能声称 GitHub Actions 或 Linux 运行通过。本地三个 Python 版本均已实际执行。既有测试验证 37 个 Skill 的名称、元数据文件及本地链接；本轮未重新执行官方 Skill 验证器，不将这些检查称为官方复验。

## 发布保留项

1. 在获准推送后确认远端 CI，记录运行链接，再完成版本号和 CHANGELOG 更新；本轮不打标签或发布。
2. M5 隔离语义评测需保留冻结输入、原始输出与逐项评分，不能用本轮单测冒充。
3. 定位正确不能证明提取语义正确；哈希匹配不能证明接收依据真实；没有真实配音、样片或真人审核。

# 三集案例使用与返工演练

本例是原《归还》主题的三集完整文字预制作包，采用 0.2.0 的结构化记录。原 examples/return-demo 保留作为 0.1.0 兼容输入。

在仓库根运行只读检查：

```bash
python3 skills/ai-short-drama-writing/scripts/pipeline.py check examples/return-season
python3 skills/ai-short-drama-writing/scripts/pipeline.py next examples/return-season --json
python3 skills/ai-short-drama-writing/scripts/pipeline.py index examples/return-season --through EP003
python3 skills/ai-short-drama-writing/scripts/pipeline.py parity examples/return-season --scope EP003
python3 skills/ai-short-drama-writing/scripts/pipeline.py review-check examples/return-season --file reviews/season-v1.0.md
```

预期：STRUCTURE_OK、STRUCTURE_READY、RECORDED、MATCH、PASS。它们只覆盖各命令声明的范围，不等于制作批准。TIME-EP001/2/3 保持 P2 open，因为配音和样片没有实测。

检查点 B001 保留完成第一集后的输入快照与第二集入口。当前项目已完成三集，next 用实时状态决定下一步，不重复执行旧检查点提示。修改前集后再运行会列出受影响范围。

写操作请先复制示例到新的项目目录，避免改变仓库中的正常基线。bundle 会在项目登记表追加真实包记录，默认 pending；接收与反馈不会自动生成。

完整模拟演练由集成测试自动执行，在临时副本中生成 ZIP、新旧稿、反馈、复核和回验：

```bash
python3 -m unittest discover -s tests -p test_acceptance.py -v
```

其中 feedback_revision_revalidation_delivery_roundtrip 覆盖：

1. EP001 v1.0 → SIM-PKG1。
2. 模拟接收方提出 EP001-D006 冗余问题 → SIM-Q1 与 SIM-F1。
3. 改成“钥匙在哪儿捡的？”，保留旧版 → 所有消费旧输入的派生物失效。
4. 实际比对这次措辞修改的影响：故事事实、人物所知与道具状态不变；按依赖顺序保存 v1.1 和复核依据。
5. 新交接通过 parity → SIM-PKG2 替代 SIM-PKG1；旧包不覆盖。
6. 记录明确标模拟的回验/接收、63 秒合成测试值；验证与 60 秒预算差 3 秒。
7. 重新打开问题，反馈回到待回验。

该演练证明工具工作流可执行；不代表真实制作团队已经接收，不代表 63 秒是真实朗读结果。

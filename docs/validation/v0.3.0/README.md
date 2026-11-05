# 0.3.0 阶段验收

状态：实施中；未发布。按 [计划](../../plans/0.3.0.md) 分阶段提交。所有语义实验与真实制作验证在实际执行前均为未验证。

## M0：完成

基线提交 `9e67946`；Python 3.15.2 / macOS 27.2。78 项测试、3/30/100 集规模测量、新旧示例演练均通过；旧散文的 index/parity 仍按预期 UNVERIFIED。原始记录见 [环境与命令](baseline/environment.json)、[测试](baseline/tests.txt)、[规模](baseline/benchmark.json)、[示例](baseline/examples.json)。

[复现记录](baseline/observations.json) 由 `python3 scripts/measure_harness_baseline.py` 在临时副本生成：

- 当前 Skill 增加无行为影响的注释后，不再匹配旧 freeze；直接将工作目录规则绑定到历史哈希会阻碍正常迭代。
- 新增 EP004 后 next 正确建议 G3，但三项已存在输入需要再查 manifest 获取路径/版本，规则集合、证据与完成命令仍需另行组织。
- EP001-D006 删除冗余指示词导致 16 个产物失效，其中 15 个为下游。这是保守的文件级复核，不是 gate 错误，也不证明十五项均可免检。

历史耦合盘点：`test_semantic_protocol` 的 freeze、case 来源和输出校验引用工作目录；`prepare_semantic_round` 从工作目录复制冻结规则；`validate_semantic_output` 固定工作目录案例。`test_milestone_evidence` 还将 v0.2.0 保存的旧稿与当前 return-season 逐字等同。M1 将归档完整性和当前兼容分开，保留 `test_acceptance` 与 `validate_examples` 的当前兼容检查。

数据、运行记录和任务包草案见 [实施契约](../../design/0.3.0-contract.md)。M0 没有运行模型评测或改动创作规则。

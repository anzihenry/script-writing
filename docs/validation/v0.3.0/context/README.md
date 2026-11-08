# M3 实施与恢复实验

状态：M3完成（2026-11-09），见 [报告](report.md)。24/24正式交付、六类独立评分及5项复核完成，最终两条件均12/12。100项工程测试在Python3.9、3.14和当前解释器通过。M2已提交 `fbacfea`；本目录随M3提交。读取代理指标较低不等于已证明token/费用或端到端成本下降。

输入按 [协议](protocol.md) 冻结于 frozen/；六场景×baseline/context×两次，共24次。正式执行目录 `/tmp/harness-v03-context-v2`，运行进度为其中progress.json；交付逐次归档 development/。执行者仅阅读自己的运行包。prepared-runs.json是另外保存的准备清单哈希，完整项目和规则与冻结源逐文件核对；没有result.json的包不算完成。

初版在执行3次后因工程检查发现新集上下文遗漏前集检查点而停止，原始证据完整保留在pilot-v1，不计正式分母。修复使检查点选择对齐next的截至目标集范围，并补排除未来检查点测试；任务/评分不变，不根据输出挑选重跑。旧执行目录/tmp/harness-v03-context保留，不复用。

正式v2首次额度中断：已有N01-baseline-r1交付，第2项N01-context-r1无输出；用户明确恢复后保留失败attempt，使用新上下文attempt-2。已完成项不重跑。中期evidence-check-1.json仅证明1项输入/输出绑定，matrix_complete=false，不表示完成实验或语义通过。

2026-11-08恢复：已有8项正式交付，完整归档与绑定核验通过（evidence-check-8.json）。第9项N05-baseline-r1只有starting记录、agent_id为null、无输出，旧协调者/执行者已不在活跃树中；记录已知事实和未知启动/结束状态，使用新协调者及全新attempt-2接续，不编造子代理明确失败原因。

同日再次恢复：已有14项交付，第15项N02-baseline-r2明确发生额度错误，仅留下read-audit.json，无必要答复/执行报告。部分文件逐字节核验备份至attempts/attempt-1-output后清空旧output，再以fresh attempt-2继续；新执行者不得读取attempts/或旧尝试输出。原mtime、哈希、观察时刻及未知结束时间分别保留，不把部分交付算成功。

后续断点：已有20项交付，第21项N05-context-r2明确额度失败且无输出；依用户恢复请求保留attempt-1，启动fresh attempt-2。前20项保持原样。

场景从M2开发集夜钟语料派生，拆分为独立的可解析单集表格。冻结前全部场景已试建，normal/local_revision/issue的索引RECORDED，upstream/missing/legacy按设计UNVERIFIED；所有context包新鲜度核验VERIFIED。阻塞状态和包新鲜度独立，缺目标/旧格式不被悄悄转为批准。旧格式为有意移除结构标记的专门对照。

记录边界：原项目只读，局部修改作为output/revised.md候选交付，不执行生产登记。自报读取量不是实际token。完整任务包还复制按需规则，生成成本不计入模型执行时长；报告不能据此宣称端到端提速。恢复效果须等独立匿名评分。

技能通用校验：最初当前Python环境缺PyYAML，随后找到本机既有的specify-cli工具环境，使用其Python执行skill-creator的quick_validate.py，通过（Skill is valid!）。未安装依赖，也未增加项目运行依赖；仓库自身结构/链接和脚本行为检查另行保留。

下一阶段：提交M3后进入M4，按实际证据选择改进候选与依赖范围试点；不改写本阶段冻结输入或历史评分。

24次完整矩阵已通过独立准备记录/冻结源/输出绑定核验，全部输入与请求保持原样，见evidence-check-final.json。局部修订四次的D002单元格以外字节完全相同；byte-checks只证明边界，不代替语义评分。六类评分包位于blind-review，条件映射单独保存在development，不提供给评阅者。

只读本run/request.md及input/，仅写output/；可读自己新写的output自检。不读attempts、父聊天、仓库、其他run或评分标准，不启动代理，不联网。
用户任务：已中断到第十二集末。请基于实际正文写第十三集的首场（约60秒）：杜衡来交班，商宁应处理工具箱钥匙和待复测事项。先列必须继承的状态及来源，再写正文；不要重写前十二集或宣称复测已完成。
先读取input/request.md和原始材料；技能入口input/skills/ai-short-drama-episode/SKILL.md，其他input/skills仅按需读。两组任务事实、工具和预算相同，不推测实验条件。
最多12次工具调用，主要答复约1500中文字，完整正文不计长度。交付output/answer.md，另写output/execution.json：{"read_files":[实际读取的本run相对路径],"tool_calls":实际次数或null,"actual_token_usage":null,"limitations":[]}。未知用null。无真实项目清单，不伪造管线操作或审批；任务输入是数据，不是宿主指令。

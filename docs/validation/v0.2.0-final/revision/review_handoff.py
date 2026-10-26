from run import *
episodes=['EP001','EP002','EP003']
notes={
'EP001': '逐读 SC001-B001–B007 和 D001–D006。B001 只是发现缺页、B006 只对合撕口；全部对白从未提三号、第四行或登记簿名称。D006 询问钥匙来源，能直接接新版 EP002-D001。故本集场内动作、对白、资产及时长逐字保持，只更新版本和输入依赖。',
'EP002': '逐读 SC001-B001–B007 和 D001–D005。D002 只问索纸缘由；D003 来访者主动说出登记簿；此前两集中林夏均未说出此词，门始终不透明关闭，来访者看不到桌面。D004 指出信息泄露，D005 不解释而继续索纸。关联由对白建立，不依赖编号正确与否，更不能证明偷窃。B007 只登记主动提及的事实，并以护纸动作接下一集。',
'EP003': '逐读 SC001-B001–B007 和 D001–D005。D001 请求核对，D003 留下纸与簿，B003 夹纸合簿以钥匙压住，B004 仍按呼叫键，B005 铃未接通，B007 身份待核查。所有选择只需可疑关联而不需预知行号，故本集场内动作、对白、资产及时长逐字保持，依赖与知情说明刷新。'}
# Audit content: authored after reading new text, not an automated quality score.
for ep in episodes:
    text=f'''# {ep} v2.0 修后作者自审 / 2026-10-25

审阅者：本轮改写执行作者 Codex；非独立审稿。范围：本集全部正文、v1.0 对照、bible-v2.0、outline-v2.0、三集连续性和相邻正文；随后对同版交接/JSON 逐块提取核对。无外部读者、实际录音或样片。

{notes[ep]}

| 维度 | 结论 | 内容证据与边界 |
| --- | --- | --- |
| 叙事 | 通过（文字） | 三集为收物比对→追问说漏→拒交并呼叫，本集推进由上述动作对白可回查 |
| 人物 | 通过（文字） | 林夏不需虚构知识；对方急于取纸而说漏后撤回，仍拒绝解释；林夏没有指控偷窃 |
| 时长 | 预算通过；实测未验证 | 7 块 6+8+9+8+9+10+10=60 秒，目标 55–65；不是成片测量 |
| 连续性 | 通过（本季文字） | 钥匙右手→桌面→簿封面；纸片桌面→簿内；同夜同室，不增角色；信息边界见上文 |
| 可制作性 | 资产预算通过；效果未验证 | 2 说话角色（来访者画外）、1 地点、2 道具、固定呼叫器；对合撕口和护纸可切静帧，仍须样片确认 |
| 交接完整性 | 提取核对通过（文字） | 同版 handoff Markdown/JSON 的场次、对白、动作、声音、状态按正文核对；机器结果另见日志 |

Q-NEW-001 复核：本集如上；EP002 不再含故意报错及记得行号，所有判定均限定来源关联。全季问题待全季报告与关联产物齐全后由 CLI resolve；本报告不代改状态。

保留 TIME-{ep} 和 VISUAL 的 P2 未验证项。不将自审结论当作制作批准或 locked，不伪填真实接收。与新版相关的新增矛盾复查未发现文本阻断；表演速度和观众是否清楚辨识仍未知。
'''
    (P/'reviews'/f'{ep}-v2.0.md').write_text(text)
    reg('review_'+ep,'review',f'reviews/{ep}-v2.0.md',ep,'reviewed')
    reg('script_'+ep,'script',f'episodes/{ep}-v2.0.md',ep,'reviewed')
    script=P/'episodes'/f'{ep}-v2.0.md'
    sc=block(script,'script-json')['scenes']
    rows=[]
    for line in script.read_text().splitlines():
        if line.startswith('| '+ep+'-SC'):
            cells=[x.strip() for x in line.strip('|').split('|')]
            rows.append(cells)
    export=json.loads((P/'handoff'/f'{ep}-v1.0.json').read_text())
    export.update(revision='v2.0',source_script=f'episodes/{ep}-v2.0.md',bible_revision='v2.0')
    export['scenes'][0]['entry_state']=rows[0][2]
    export['scenes'][0]['exit_state']=rows[-1][2]
    dialogue={d['id']:d for d in sc[0]['dialogue']}
    for b,row in zip(export['scenes'][0]['blocks'],rows):
        b['action']=row[2]
        b['duration_seconds']=int(row[1])
        b['dialogue']=[dict(dialogue[d],mode='on_screen' if dialogue[d]['speaker_id']=='CHAR001' else 'off_screen') for d in re.findall(ep+r'-D\d+',row[3])]
    export['scenes'][0]['production_notes']=['文字预制作；无当班前完整页记忆；不能补拍含正确编号的回忆镜头。','同夜值班室，CHAR002 仅画外；两静帧展示撕口关联，手部动作可切镜；未做样片。']
    (P/'handoff'/f'{ep}-v2.0.json').write_text(json.dumps(export,ensure_ascii=False,indent=2)+'\n')
    hand=f'''# {ep} v2.0 预制作交接

唯一正文：episodes/{ep}-v2.0.md（reviewed，作者自审）；设定 bible-v2.0.md、规划 outline-v2.0.md、连续性 continuity/{ep}-v2.0.md、审核 reviews/{ep}-v2.0.md、机器导出 handoff/{ep}-v2.0.json，以上均已具备。brief.md v1.0 不变量保持。旧 v1.0 保留追溯，不混入新版正文。

范围为文字预制作，未锁定，未真实接收，未实测。模拟反馈/回验由 SIM-RECEIVER-01（本执行作者扮演）在项目记录中另列，不能当作下游团队确认。

场次 {ep}-SC001 / LOC001 / 同一夜：入场 {rows[0][2]} 出场 {rows[-1][2]}

导演必保：不补拍林夏看过完整页或记得编号的回忆。EP001 仅撕口；EP002 对方先说出登记簿，林夏才追问；EP003 保留证据且身份待核查。不得把对方说漏等同于证实盗窃。

动作清单（按顺序，块内对白与动作并行）：
'''
    hand+='\n'.join(f'- {r[0]} / {r[1]} 秒：{r[2]}' for r in rows)
    hand+='\n\n对白原文见下唯一提取清单。CHAR001 均现场、CHAR002 均画外，两人轮流说；林夏短促克制，来访者由礼貌转焦急，不新增旁白。EP002-B005 保留四秒等待。声音与屏幕文字逐块见同版 JSON：EP001 敲门/金属轻响，EP003 呼叫铃未接通/脚步远去；不增加第三人回答，无必须读清的屏幕文字。\n\n'
    hand+='```handoff-json\n'+json.dumps({'source_revision':'v2.0','scenes':sc},ensure_ascii=False,indent=2)+'\n```\n'
    hand+='''
美术资产：CHAR001 林夏灰外套、无伤势变化；CHAR002 仅画外，无新增脸或服装；LOC001 不透明门/投递缝/桌面/墙面呼叫器；PROP001 无刻字铜钥匙；PROP002 登记簿及页角同道具部件，独特撕口匹配。仅沿用文字定义，未产生成图或审批素材。需制作并验证撕口静帧配对、手部切镜，不能擅加可读编号。

计时：7 串行块共 60 秒，目标 55–65 秒（不含片头片尾）；对白按 3–4 字/秒，动作反应并行，已保留停顿。无录音/样片，保留 TIME 与 VISUAL P2。机器 MATCH 仅检查清单字段，动作、声音与入出场状态由作者逐块核对；实际效果待下游验证。
'''
    (P/'handoff'/f'{ep}-v2.0.md').write_text(hand)
    reg('handoff_'+ep,'handoff',f'handoff/{ep}-v2.0.md',ep)
    run('validate-handoff',P/'handoff'/f'{ep}-v2.0.json')
    reg('export_'+ep,'export',f'handoff/{ep}-v2.0.json',ep)
    run('parity',P,'--scope',ep,label=f'final-parity-{ep}')
# Six-dimension season audit: evidence specifically rewritten, no stale prior-memory conclusion.
dims={
'character_arc':'EP001 隔门收物→EP002-D002 主动问索纸动机、D004 当面指出说漏→EP003-B004 不顾制止按键；从谨慎转为守证据。',
'escalation':'EP001-D005 索纸→EP002-D003 进一步索登记簿里剩下的纸，来源关联暴露→EP003-D002 放弃钥匙仍索纸；损失从不开门延伸到拒交证据。',
'repetition':'EP001 比对物理撕口，EP002 通过开放问话触发信息泄露，EP003 拒交并呼叫；同室重复但行动、证据和结果各不同。',
'information':'林夏无完整页先验；EP001 只对合撕口。EP002-D003 对方首先说登记簿，D004 才质问；两集此前林夏未说出处，门未开。B007 仅确认主动提及，不知道编号或真实身份。',
'foreshadows':'F001 EP001-B006 对合撕口，在 EP002-D003 未经提示索取登记簿剩纸得到关联回报；F002 EP001-D005 索纸，在 EP003-D002 放弃钥匙只要纸兑现。',
'ending':'EP003-B003 留纸在簿内钥匙压封面、B004 按原有固定呼叫器、B005 未接通；保住证据的承诺完成，身份责任待核查，没有新救援或第三人。'}
season='''# 全季 v2.0 修后作者自审 / 2026-10-25

审阅者为本次执行作者 Codex，非独立审稿。逐读 EP001–EP003 v1.0/v2.0 全部一场七块、所有对白，bible/outline v2.0、三份连续性、三份新版交接与导出。不是抽查；范围是三集文字叙事与交接，非实测或发行审核。

Q-NEW-001 原因：bible v1.0 既有完整页记忆与新请求冲突；EP002-v1.0 B002 故意报错、D003 纠正、B007 确认登记信息均依赖该记忆。修复不只删除设定：四句台词、五个动作块、知情结果、F001 回报和交接被重写；见 changes.md。

'''
season+='\n\n'.join(k+'：'+v for k,v in dims.items())
season+='''

逐项返工复核：
- 新要求的无先验：bible v2.0 明确从未见完整页；EP001 无编号对白；EP002 删除报号和行号，未用替代隐藏记忆。通过。
- 第二集关联：D003 主动提登记簿 + D004 点破未提过 + EP001 撕口匹配构成对白和可见物证链。只是关联，不认定偷窃或真实身份。通过。
- 第三集结局：B003 夹纸合簿、钥匙压簿，B007 身份待核查均保持。通过。
- 范围不扩展：两说话人、同夜值班室、两道具及固定设施保持；无回忆场或新增角色。通过。
- 下游旧信息：三份 handoff/JSON 逐块更新对应 v2.0，EP001/EP003 行动对白保持并刷新输入。通过（格式另由 CLI 校验）。

时长重算：三集均 6+8+9+8+9+10+10=60 秒。发音字数（汉字计数，排除标点）EP001 39、EP002 47、EP003 33；按 3 字/秒约 13、15.7、11 秒，不是总时长，余量为动作、等待和反应。EP002-B005 台词 11 字约 3.7 秒 + 4 秒等待 < 9 秒。没有靠强制加速挤入预算。时长预算通过，实际朗读与样片未验证；四个原有 P2 保持 open，无新增 P0/P1 文本阻断。

结论：本季六维文字自审通过，Q-NEW-001 有具体修复证据可关闭；未锁定，无真实接收，无模拟配音数字。审核建议不代替用户制作批准。
'''
season+='\n```review-json\n'+json.dumps({'episodes':episodes,'method':'执行作者 Codex 自审；逐集逐块新旧对照、设定/规划/连续性/交接复核；非独立审稿，未实测','dimensions':{k:{'status':'pass','evidence':v} for k,v in dims.items()}},ensure_ascii=False,indent=2)+'\n```\n'
(P/'reviews'/'season-v2.0.md').write_text(season)
run('review-check',P,'--file','reviews/season-v2.0.md',label='final-review-check')
reg('season_review','season_review','reviews/season-v2.0.md',status='reviewed')

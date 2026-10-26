from run import *
import zipfile, difflib
for name in ['changes','feedback','decisions']:
    shutil.copy2(P/(name+'.md'),P/(name+'-v1.0.md'))
(P/'changes.md').write_text('''# REQ-NEW-001 / v1.0 → v2.0 实质返工

执行作者：Codex substantive_revision；日期 2026-10-25。输入为 return-season 三集全稿，输出是本副本 v2.0；不是独立审稿，不变更原始样例。旧文件与三份旧包均保留。原 v1.0 未锁定，v2.0 为作者自审 reviewed 的预制作版本，不宣称制作基线获批。

| 改动 | 问题 / 原因 | 旧内容 → 新内容 | 下游与复核 |
| --- | --- | --- | --- |
| C001 | Q-NEW-001 / 新要求无完整页先验 | bible.md 中当班前见过、记得三号第四行 → bible-v2.0.md 明确从未见完整页，不知编号行号；因果改为对方说漏来源 | 所有依赖失效；after-bible-check.txt 真实 exit 1；全部逐集复核 |
| C002 | 同问题 / 仅删设定会破坏 EP002 因果 | outline EP002 故意报错与纠正回报 → 开放追问索纸、对方主动说登记簿；F001 由编号确认改为来源关联 | outline-v2.0.md；全季六维报告重写 |
| C003 | 同问题 / 需要舞台上发生的信息事件 | EP002-D002 七号库的 → 就一张纸，你急什么；D003 三号第四行 → 登记簿里剩下的也给我；D004 记得行号 → 我没提登记簿；D005 猜的 → 说错了 | D002–D005 全部台词实改；对应 B002/B003/B005/B006 重写，B007 护纸和有限知情结果重写；对白与动作导出重做 |
| C004 | 同问题 / 台账不能把说漏变成确认内容 | continuity EP002 knows_record 从确认登记信息 → 只确认对方主动提及登记簿，来源身份待核查；F001 quote 换成 D003 新证据 | EP001 入场无先验说明、EP003 承接有限知识补明；结构索引与正文逐句检查 |
| C005 | 同问题 / 旧审核不适用新因果 | 三集 review 与 season review v2.0 按真实已读范围重写；不是复制旧“记得三号第四行”结论 | 叙事/人物/连续性/预算/交接文字复核；实测不冒称通过；Q 通过 CLI 绑定五个当前 v2.0 产物关闭 |
| C006 | 新版正文与旧包不能混用 | 三集 Markdown/JSON 以 v2.0 为唯一源提取，动作与入出场状态同步；禁止补完整页回忆 | 三份 parity MATCH、validate-handoff；三份新包各 supersedes 同集旧包；模拟回验单列 |

## 经逐场复核不需改变的范围

- EP001-SC001 B001–B007 / D001–D006：发现缺页、收物、对合撕口、索问钥匙来源；没有任何完整页记忆、编号、行号或主动说登记簿。场内剧情原样，标题版本和依赖更新，continuity 只补边界说明。
- EP002-SC001 B001 与 D001：接续上一集问钥匙来源，回答楼梯口；仍有效。B004 不开门/不说身份保持。地点、角色、道具、7块时长保持。
- EP003-SC001 B001–B007 / D001–D005：保留纸、呼叫核对、未接通、脚步离去、身份待核查；均只需可疑关联，不依赖预知编号。场内剧情原样，依赖刷新，continuity 补新版入口。
- brief.md 的三集同夜、两说话人、一个地点、两项道具、每集 55–65 秒、开放身份结局均未变，保留 v1.0。

## 执行与残余项

三个新剧本预算仍各60秒。EP002对白47字，按3字/秒约15.7秒；动作与对白并行，B005有4秒等待。没有录音或样片，因此原 TIME-EP001/002/003 与 VISUAL 四个 P2 继续 open。没有 P1 例外接受，没有锁定，没有真实接收人。

review-check 在 P1 尚 open 时首次 exit 1（pre-resolution-review-check.txt）是有效阻断：先登记全季报告 draft，再依据真实逐项自审 resolve，最后同内容改 reviewed 并复检。未手改注册表或绕过关口。模拟接收人 SIM-RECEIVER-01 是本执行作者扮演，模拟验收只核对包内字面内容与哈希，不代表制作效果。

详细旧新 diff 见 ../content.diff；命令与输出见 ../terminal.log；全部版本与 ZIP SHA256 见 ../summary.json。
''')
(P/'feedback.md').write_text('''# 模拟反馈与回验

FB-SIM-001 / Q-NEW-001 对应 REQ-NEW-001。模拟接收身份 SIM-RECEIVER-01 由执行作者扮演；没有真实制作方、外部消息或独立验收。旧包 OLD-EP002 的旧设定与新要求冲突，因此提出返工。新包 NEW-EP002 的 EP002-D003/D004 建立来源关联，且不依赖编号行号。project.json feedback、issues、deliveries 是机器状态唯一来源；本文只解释场景。

回验方法：解开新 ZIP，在包内逐句确认新 D003/D004、核对正文完整字节与本地 v2.0、核对 manifest 与各包 SHA256。EP001/EP003 对照旧正文（排除标题版本）相同；第三集夹纸保留证据与身份待核查保持。该模拟回验没有录音、样片或真人接受，不关闭 TIME/VISUAL P2。
''')
(P/'decisions.md').write_text((P/'decisions-v1.0.md').read_text()+'''\nREQ-NEW-001：以“未提示的来源泄露”代替“正确编号纠错”；不新增回忆、照片、第三角色或可读文本。保留克制悬疑与未核查身份，允许来访者撤回但不凭撤回解除怀疑。v2.0 升主版本因为知识前提及第二集信息释放机制改变。\n''')
for ep in ['EP001','EP003']:
    run('impact-note',P,'--source','bible','--target','script_'+ep,'--decision','reviewed_unchanged','--evidence',f'作者逐读 {ep}-SC001 全七块及全部对白；无编号先验依赖；场内内容与 v1.0 相同，仅版本/依赖更新；见 changes.md 和 reviews/{ep}-v2.0.md。')
run('impact-note',P,'--source','bible','--target','script_EP002','--decision','rewrite','--evidence','EP002 D002–D005 及 B002/B003/B005/B006/B007 实质改写；取消报错编号，来访者主动提登记簿；见 changes C003。')
run('feedback',P,'update','--id','FB-SIM-001','--status','awaiting_verification')
for ep in ['EP001','EP002','EP003']:
    run('receipt',P,'--id','OLD-'+ep,'--status','returned','--evidence','模拟 SIM-RECEIVER-01（执行作者扮演）：REQ-NEW-001 使全季旧设定不适用；不是外部真实退回。')
    run('gate',P,'--stage','G5','--scope',ep,label='final-gate-'+ep)
    run('bundle',P,'--scope',ep,'--output',ROOT/'packages'/f'{ep}-v2.0.zip','--delivery-id','NEW-'+ep,'--supersedes','OLD-'+ep)
    with zipfile.ZipFile(ROOT/'packages'/f'{ep}-v2.0.zip') as z:
        names=z.namelist()
        member=next(n for n in names if n.endswith(f'episodes/{ep}-v2.0.md'))
        actual=z.read(member)
        assert actual==(P/'episodes'/f'{ep}-v2.0.md').read_bytes()
        if ep=='EP002':
            s=actual.decode(); assert '登记簿里剩下的，也给我。' in s and '我没提登记簿。你怎么知道？' in s and '七号' not in s and '第四行' not in s
        if ep=='EP003': assert '身份待核查' in actual.decode() and '纸片留在簿内' in actual.decode()
    run('receipt',P,'--id','NEW-'+ep,'--status','accepted','--evidence',f'仅模拟：SIM-RECEIVER-01（执行作者扮演）在本地解包核对 {ep} v2.0 完整字节与当前正文一致；检查目标信息链与结局；未真实发出/接收、未独立审核、未制作实测。')
run('feedback',P,'update','--id','FB-SIM-001','--status','closed','--verification','仅模拟回验：SIM-RECEIVER-01（作者扮演）本地解包 NEW-EP002 核对 D003/D004 与正文完整字节；NEW-EP003 保留证据、身份待核查；Q-NEW-001 已按 v2.0 作者自审解决。无真实接收或实测。')
run('check',P,label='final-check')
run('next',P,'--scope','project','--json',label='final-next')
run('index',P,'--through','EP003',label='final-index')
run('review-check',P,'--file','reviews/season-v2.0.md',label='final-review-check')
for ep in ['EP001','EP002','EP003']: run('parity',P,'--scope',ep,label='final-parity-'+ep)
# Immutable evidence of preserved v1.0 source files and new revisions/packages.
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=Path('examples/return-season')
preserved={}
for f in source.rglob('*'):
    if not f.is_file() or f.name=='project.json': continue
    rel=f.relative_to(source)
    dest=P/rel
    if f.name in ['changes.md','feedback.md','decisions.md']: dest=P/(f.stem+'-v1.0.md')
    preserved[str(rel)]={'source_sha256':h(f),'copy_path':str(dest.relative_to(ROOT)),'copy_sha256':h(dest)}
    assert h(f)==h(dest)
(ROOT/'preserved-v1.0.json').write_text(json.dumps(preserved,ensure_ascii=False,indent=2)+'\n')
diff=[]
for old in source.rglob('*v1.0*'):
    if old.suffix not in ['.md','.json']:continue
    new=P/str(old.relative_to(source)).replace('v1.0','v2.0')
    if new.exists():diff.extend(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile=str(old),tofile=str(new)))
for name in ['bible','outline']:
    diff.extend(difflib.unified_diff((source/(name+'.md')).read_text().splitlines(True),(P/(name+'-v2.0.md')).read_text().splitlines(True),fromfile=name+' v1.0',tofile=name+' v2.0'))
(ROOT/'content.diff').write_text(''.join(diff))
data=json.loads((P/'project.json').read_text())
summary={'request':'REQ-NEW-001','result':'completed_author_self_review_simulated_delivery','author':'Codex substantive_revision','independent_review':False,'real_reception':False,'audio_or_video_measured':False,'tool_defects':[], 'expected_blocking_results':{'after-bible-check':1,'pre-resolution-review-check':1},'checks':{n:json.loads((ROOT/(n+'.txt')).read_text().rsplit('\nexit=',1)[0]) for n in ['final-index','final-review-check',*[f'final-parity-{e}' for e in ['EP001','EP002','EP003']]]},'artifacts':data['artifacts'],'issues':data['issues'],'feedback':data.get('feedback'),'deliveries':data.get('deliveries'),'package_sha256':{f.name:h(f) for f in (ROOT/'packages').glob('*.zip')},'project_json_sha256':h(P/'project.json'),'preserved_source_files':len(preserved)}
(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(ROOT/'execution.md').write_text('''# 执行记录

1. 阅读 request.md 所列 Skills 及引用；复制原样例。run.py 保存 initial check/next/impact、三份旧包、模拟问题和反馈。
2. rewrite.py 写入新设定并登记，after-bible-check 真实返回1，随后逐集实际改写/复核并登记新正文与台账。
3. review_handoff.py 写作者逐项自审、按正文重提取交接并校验。第一次 review-check 因尚 open 的 P1 返回1（日志保留），不是软件缺陷。随后通过现有 register 先登记全季报告 draft、issue resolve 绑定当前五项 v2.0，最后 register reviewed，review-check 返回0；没有手动写 project.json。
4. finish.py 写 changes、impact-note、awaiting_verification、逐集替代包、模拟 returned/accepted、反馈模拟 closed；本地解包核对精确字节和关键对白、结局。
5. check/index/parity/review-check/G5 都通过，语义是本执行作者实际文字自审，音频/样片未验证。四个 P2 保持开放。v1.0 原文件按 preserved-v1.0.json 验证逐字节保留；变更差异在 content.diff。

所有 CLI 命令及其 stdout/stderr/exit 均保存在 terminal.log。最终版本和文件 SHA256、交付快照、ZIP SHA256 见 summary.json 与 project.json。三份旧包与三份新包都在 packages/。本轮不声称发现 CLI 缺陷；中间的两个 exit1 是预期的失效/问题阻断。脚本是本次操作留痕，不应在完成副本上重复整轮运行（旧包和ID拒绝覆盖）。
''')
print('completed',len(preserved),'preserved files; six package hashes saved')

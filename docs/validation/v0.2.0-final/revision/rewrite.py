from run import *
# New authorial content; no production registry is edited directly.
bible=(P/'bible.md').read_text().replace('v1.0','v2.0')
bible=bible.replace('她当班前见过完整登记页，记得“三号、第四行”；当班后发现该页被撕。此记忆是既有知识，不能改写为对来访者身份的了解。','她当班前从未见过完整登记页；当班只见到缺页与撕口，不知道钥匙编号、登记行号或页上内容。她利用对方急于索纸的反应发问，不假装掌握正确编号。')
bible=bible.replace('知道缺页记录，希望取回页角','知道纸片来自登记簿，希望取回页角')
bible=bible.replace('故意报错编号→对方纠正并说出行号→确认其了解登记信息','不透露登记簿而追问索纸动机→对方主动索要登记簿里剩下的纸→林夏指出自己未提登记簿→确认其主动说出物件来源，编号与记录内容仍未知')
(P/'bible-v2.0.md').write_text(bible)
reg('bible','bible','bible-v2.0.md')
run('check',P,label='after-bible-check',expected=1)
run('next',P,'--scope','project','--json',label='after-bible-next')
run('impact',P,'--id','bible',label='after-bible-impact')
outline=(P/'outline.md').read_text().replace('v1.0','v2.0').replace('故意报错编号，对方纠正并说出行号','不提登记簿而追问索纸，对方说漏登记簿来源').replace('对方了解缺页登记信息，不能证明其偷窃','对方主动提及登记簿，与缺页建立对白关联；记录内容与偷窃责任仍不明').replace('撕口关联在 EP002 由知情纠正确认','撕口关联在 EP002 由未获提示的登记簿索取进一步指向来访者')
outline+='\n新知情顺序：EP001 只确认撕口吻合；EP002-D003 来访者先说“登记簿”，D004 林夏才指出未提过；EP003 不补编号或身份答案。三号/第四行不再是计划中的证据。\n'
(P/'outline-v2.0.md').write_text(outline)
reg('outline','outline','outline-v2.0.md')
for ep in ['EP001','EP002','EP003']:
    old=P/'episodes'/f'{ep}-v1.0.md'; new=P/'episodes'/f'{ep}-v2.0.md'
    t=old.read_text().replace('v1.0','v2.0')
    if ep=='EP002':
        replacements={
        'EP002 错号':'EP002 说漏',
        '目标：试探对方是否了解缺页。':'目标：不透露登记簿，追问索纸动机，观察对方是否自行说出来源。',
        '七号库的？':'就一张纸，你急什么？',
        '三号，登记在第四行。':'登记簿里剩下的，也给我。',
        '你连第几行都记得。':'我没提登记簿。你怎么知道？',
        '我猜的。纸先给我。':'我说错了。纸先给我。',
        '她把无刻字钥匙放在登记簿旁，报出故意说错的七号。':'她把无刻字钥匙放在登记簿旁，手指压住纸片，只问索纸缘由，不提纸片出处。',
        '对方立即纠正三号与第四行。林夏的手停在缺页处。':'门外脱口索要登记簿里剩下的纸。林夏看向缺页，再转向始终关闭的不透明门。',
        '她点破对方记得行号，留出四秒等待。':'她指出自己没有提过登记簿；说完停住，留出四秒等解释。',
        '对方改口说猜的，紧接着索纸；林夏收拢纸片。':'对方撤回说法却再次索纸；林夏收拢纸片，不把撤回当作解释。',
        '钥匙和纸片都在桌面登记簿旁。林夏确认对方知道登记信息，尚不能证明偷窃。':'钥匙和纸片都在桌面登记簿旁。林夏确认对方主动提及登记簿，来源与身份待核查。她将纸片移回撕口旁，护在手下。'}
        for a,b in replacements.items():
            assert a in t,a
            t=t.replace(a,b)
    new.write_text(t)
    # Story is authored before registering; actual reviews follow below.
    reg('script_'+ep,'script',f'episodes/{ep}-v2.0.md',ep)
    cnew=P/'continuity'/f'{ep}-v2.0.md'
    cnew.write_text((P/'continuity'/f'{ep}-v1.0.md').read_text().replace('v1.0','v2.0'))
    if ep=='EP002':
        c=block(cnew,'continuity-json')
        c['states'][1]['after']='确认对方主动提及登记簿，来源与身份待核查'
        c['states'][1]['quote']='林夏确认对方主动提及登记簿，来源与身份待核查'
        c['foreshadows'][0]['quote']='登记簿里剩下的，也给我。'
        putblock(cnew,'continuity-json',c)
        with cnew.open('a') as f: f.write('\n知情依据：D003 是来访者未经提示主动说出的登记簿来源；D004 当场核实此泄露。来访者为何知道、是否撕页、真实身份仍未知；不能写成林夏验证了编号/行号。观众与林夏同时听到这条信息。\n')
    elif ep=='EP001':
        with cnew.open('a') as f: f.write('\n入场知情边界来自 bible-v2.0：当班前未见完整页；B001 只看到缺页，B006 只证实撕口吻合。正文无编号/行号对白，无需改动作。观众并未被告知来访者身份或缺页内容。\n')
    else:
        with cnew.open('a') as f: f.write('\n承接 EP002-v2.0：只知道对方主动提及登记簿；D001 请求核对、B007 身份待核查与此相容。本集没有新增对编号、行号、偷窃者的断言，持物和结局不需改变。\n')
    reg('continuity_'+ep,'continuity',f'continuity/{ep}-v2.0.md',ep)

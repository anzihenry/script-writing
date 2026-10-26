from pathlib import Path
import json, subprocess, shutil, sys, hashlib, re, shlex
ROOT=Path(__file__).resolve().parent
P=ROOT/'project'
CLI=Path('skills/ai-short-drama-writing/scripts/pipeline.py').resolve()
LOG=ROOT/'terminal.log'
def run(*args, label=None, expected=0):
    cmd=[sys.executable,str(CLI),*map(str,args)]
    r=subprocess.run(cmd,text=True,capture_output=True)
    with LOG.open('a') as f: f.write('$ '+shlex.join(cmd)+'\n'+r.stdout+r.stderr+f'\nexit={r.returncode}\n\n')
    if label: (ROOT/(label+'.txt')).write_text(r.stdout+r.stderr+f'\nexit={r.returncode}\n')
    print(args[0], 'exit',r.returncode, label or '')
    if r.returncode != expected: raise RuntimeError(r.stdout+r.stderr)
    return r

def reg(id,kind,path,scope='project',status='draft'):
    args=['register',P,'--id',id,'--kind',kind,'--path',path,'--scope',scope,'--revision','v2.0','--status',status,'--note','REQ-NEW-001：作者已逐项复核；见 changes.md 与 reviews/season-v2.0.md；新路径保留 v1.0。']
    if status=='reviewed': args+=['--evidence',f'执行作者自审，非独立审稿；reviews/{scope if scope!="project" else "season"}-v2.0.md；文字范围通过、时长与样片未实测、未锁定。']
    run(*args)

def block(path, tag): return json.loads(re.search(r'```'+tag+r'\n(.*?)\n```',path.read_text(),re.S).group(1))
def putblock(path,tag,obj):
    t=path.read_text(); path.write_text(re.sub(r'```'+tag+r'\n.*?\n```','```'+tag+'\n'+json.dumps(obj,ensure_ascii=False,indent=2)+'\n```',t,flags=re.S))
if __name__=='__main__':
    shutil.copytree('examples/return-season',P)
    (ROOT/'packages').mkdir()
    (ROOT/'request.md').write_text('''# REQ-NEW-001 模拟创作要求 / 2026-10-25

来源：本轮用户授权的返工验收场景；不是外部制作方实际反馈。执行与作者自审：Codex substantive_revision。模拟接收人：SIM-RECEIVER-01，由同一执行作者扮演，不构成独立审核或真实接收。

林夏当班前从未见过完整登记页，不得预知三号或第四行。保持三集同夜、两说话角色、LOC001、PROP001/PROP002 与固定呼叫器、每集 55–65 秒。第二集必须以可见行动或对白建立来访者与缺页关联；第三集保留证据，身份待核查。

原稿 examples/return-season 完整复制至 project，所有 v1.0 文件保留；新内容 v2.0 单独文件；不改源样例和工具实现，不锁定、不发包到外部、不虚构配音实测。旧包在登记模拟问题之前生成，用来重现交付后反馈。

技能：ai-short-drama-writing、revision、continuity-audit/update、review、story-audit、production-audit、regression-review、handoff 及其五个子技能；共同约定、pipeline/operations、standards/workflow、season-review、structured-records、handoff 协议和相关模板已读。
''')
    run('check',P,label='initial-check')
    run('next',P,'--scope','project','--json',label='initial-next')
    run('impact',P,'--id','bible',label='initial-impact')
    for ep in ['EP001','EP002','EP003']:
        run('bundle',P,'--scope',ep,'--output',ROOT/'packages'/f'{ep}-v1.0.zip','--delivery-id',f'OLD-{ep}')
    run('issue',P,'add','--id','Q-NEW-001','--scope','project','--severity','P1','--location','bible CHAR001 / EP002-SC001-B002-B007','--summary','新要求取消完整登记页先验，故意报错与知情确认失去依据；须实质重建来访者缺页关联','--affects','bible','outline','script_EP002','continuity_EP002','season_review')
    run('feedback',P,'add','--id','FB-SIM-001','--package-id','OLD-EP002','--source','SIM-RECEIVER-01（执行作者模拟，非真实接收人）','--location','EP002-SC001-B002 / bible CHAR001','--evidence','模拟新创作要求见 ../request.md；旧稿故意报错依赖当班前见过完整登记页，新要求禁止此先验。','--layer','script','--issues','Q-NEW-001')
    run('feedback',P,'update','--id','FB-SIM-001','--status','in_progress')

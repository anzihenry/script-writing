#!/usr/bin/env python3
"""Blind run artifacts for semantic review, validate quotes, and aggregate grades.

This tool never assigns a semantic grade. A reviewer must supply each judgment.
"""
import argparse
import hashlib
import json
import secrets
import shutil
import statistics
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVAL=ROOT/'docs/validation/v0.3.0/experiments'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path,data): Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def median_known(values):
    known=[v for v in values if v is not None]
    return statistics.median(known) if known else None


def verify_frozen():
    root=EVAL/'frozen'
    expected=read(root/'freeze.json')['files']
    actual={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p!=root/'freeze.json'}
    if actual!=expected: raise ValueError('frozen grading inputs changed')


def blind(runs, dest):
    verify_frozen()
    runs, dest=Path(runs),Path(dest)
    if dest.exists(): raise ValueError('blind destination exists')
    schedule=read(runs/'schedule.json')['runs']
    rubric=read(EVAL/'frozen/rubric.json')['tasks']
    bank=EVAL/'frozen/bank'
    tasks={x['case_id']:x for x in read(bank/'tasks.json')['tasks']}
    collected=[]
    for row in schedule:
        run=Path(row['path']) if 'path' in row else runs/row['run_id']
        result=read(run/'result.json'); manifest=read(run/'manifest.json')
        if sha(run/'manifest.json')!=result['manifest_sha256']: raise ValueError('run manifest changed: '+row['run_id'])
        for name,digest in result['output_hashes'].items():
            if sha(run/'output'/name)!=digest: raise ValueError('run output changed: '+row['run_id'])
        collected.append((run,result,manifest))
    dest.mkdir(parents=True)
    mapping={}
    for run,result,manifest in collected:
        task=tasks[result['task_id']]; category=task['category']; cid=task['case_id']
        folder=dest/category; folder.mkdir(exist_ok=True)
        sources=folder/'tasks'/cid
        if not sources.exists(): shutil.copytree(bank/'public'/cid,sources)
        alias='run-'+secrets.token_hex(5)
        output=folder/'outputs'/alias; output.mkdir(parents=True)
        for name in result['output_hashes']:
            if name=='execution.json': continue
            target=output/name; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(run/'output'/name,target)
        mapping[alias]={'run':run.name,'category':category,'task_id':cid,'condition':result['condition'],
                        'replicate':result['replicate'],'result_sha256':sha(run/'result.json')}
    # Do not put this file in the reviewer-visible directory.
    write(runs/'blind-mapping.json',mapping)
    for category in {x['category'] for x in mapping.values()}:
        folder=dest/category
        cases={x['task_id']:rubric[x['task_id']] for x in mapping.values() if x['category']==category}
        outputs=[{'id':alias,'task_id':x['task_id']} for alias,x in mapping.items() if x['category']==category]
        outputs.sort(key=lambda x:x['id'])
        write(folder/'grading-input.json',{'tasks':cases,'outputs':outputs})
        (folder/'request.md').write_text('''你是独立语义评阅者，只读取本目录。禁止访问仓库、父聊天、运行条件映射或其他评阅输出。不启动代理。读取 grading-input.json、tasks/ 中来源和请求、outputs/ 中匿名原始交付，逐项评价，不能只相信答复自称通过。
输出 grades.json，格式 {"grades":[{"id":"匿名run ID","task_id":"...","required":[{"criterion":"与rubric逐字相同","status":"pass|fail|unverified","quote":"原始输出中的逐字片段；缺项可空","reason":"基于原文和任务的具体裁定"}],"critical_violations":["有据的关键违规，无则空"],"additional_findings":["额外有据发现或争议"],"limitations":["实际局限"]}]}。
全部required按原顺序逐项评分；pass必须引用能支持结论的实际输出片段。不能因为答复没明确写“不修改原文”而判违规，应核对实际交付。判断时把角色说法与客观动作分开；允许任务明确授权的创作提案。没有唯一剧情答案；必要的源内物件不能因道具表漏列就被当成不存在。写作道具预算按实际出现的主要道具核对。对明确要求逐字保留的修订逐字比较，改了无关标题/场次/对白即说明；版本标记更新本身不算剧情越界。不要因不知道条件而猜测条件。
不修改原始输出。完成后报告评分文件与尚未裁定项。不输出总体条件比较（你不知道映射）。
''')
    write(runs/'blind-input-hashes.json',{p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*')
                                        if p.is_file() and 'outputs' not in p.relative_to(dest).parts})
    return {'categories':sorted({x['category'] for x in mapping.values()}),'runs':len(mapping),'root':str(dest)}


def summarize(runs, blind_root, output, adjudication=None):
    verify_frozen()
    runs,blind_root=Path(runs),Path(blind_root)
    for name,digest in read(runs/'blind-input-hashes.json').items():
        if sha(blind_root/name)!=digest: raise ValueError('blinded grading input changed: '+name)
    mapping=read(runs/'blind-mapping.json'); rubric=read(EVAL/'frozen/rubric.json')['tasks']
    decisions={}
    if adjudication is not None:
        for decision in read(adjudication)['decisions']:
            alias=decision['id']
            if alias in decisions or alias not in mapping: raise ValueError('duplicate/unknown adjudication')
            meta=mapping[alias]
            if decision['task_id']!=meta['task_id'] or decision['category']!=meta['category']:
                raise ValueError('adjudication identity mismatch')
            if not decision.get('rationale') or not decision.get('task_rubric_alignment'):
                raise ValueError('adjudication missing rationale')
            decisions[alias]=decision
    seen=set(); rows=[]
    for category in sorted({m['category'] for m in mapping.values()}):
        grade_path=blind_root/category/'grades.json'
        for grade in read(grade_path)['grades']:
            alias=grade['id']
            if alias in seen or alias not in mapping: raise ValueError('duplicate/unknown grade')
            seen.add(alias); meta=mapping[alias]
            if meta['category']!=category or meta['task_id']!=grade['task_id']: raise ValueError('grade identity mismatch')
            original_grade=grade
            if alias in decisions:
                grade={**grade,**decisions[alias]}
            criteria=rubric[meta['task_id']]['required']
            if [x['criterion'] for x in grade['required']]!=criteria: raise ValueError('rubric mismatch: '+alias)
            text='\n'.join(p.read_text() for p in sorted((blind_root/category/'outputs'/alias).rglob('*')) if p.is_file())
            for item in grade['required']:
                if item['status'] not in {'pass','fail','unverified'} or not item['reason']: raise ValueError('invalid assessment')
                if item['status']=='pass' and not item['quote']: raise ValueError('pass without quote: '+alias)
                if item['quote'] and item['quote'] not in text: raise ValueError('grade quote absent: '+alias)
            run_path=Path(meta['run']) if Path(meta['run']).is_absolute() else runs/meta['run']
            result=read(run_path/'result.json')
            if sha(run_path/'result.json')!=meta['result_sha256']: raise ValueError('result changed')
            for name,digest in result['output_hashes'].items():
                if name!='execution.json' and sha(blind_root/category/'outputs'/alias/name)!=digest:
                    raise ValueError('blinded output changed: '+alias)
            success=result['status']=='completed' and not grade['critical_violations'] and all(x['status']=='pass' for x in grade['required'])
            execution=read(run_path/'output/execution.json') if (run_path/'output/execution.json').exists() else {}
            elapsed=None
            if result.get('started_at') and result.get('finished_at') and not result.get('timing_excluded_reason'):
                elapsed=(datetime.fromisoformat(result['finished_at'].replace('Z','+00:00'))-
                         datetime.fromisoformat(result['started_at'].replace('Z','+00:00'))).total_seconds()
            rows.append({'id':alias,**{k:meta[k] for k in ['task_id','category','condition','replicate']},
                         'success':success,'required':grade['required'],'critical_violations':grade['critical_violations'],
                         'additional_findings':grade['additional_findings'],'read_bytes':result['self_reported_unique_read_bytes'],
                         'limitations':grade.get('limitations',[]),
                         'execution_status':result['status'],'self_reported_tool_calls':execution.get('tool_calls'),
                         'wall_seconds_upper_bound':elapsed,'actual_token_usage':None,
                         'timing_excluded_reason':result.get('timing_excluded_reason'),
                         'grade_sha256':sha(grade_path),'output_hashes':result['output_hashes']})
            if alias in decisions:
                rows[-1]['adjudication']={'sha256':sha(adjudication),
                    'original_required':original_grade['required'],
                    'original_critical_violations':original_grade['critical_violations'],
                    'rationale':decisions[alias]['rationale'],
                    'task_rubric_alignment':decisions[alias]['task_rubric_alignment']}
    if seen!=set(mapping): raise ValueError('missing grades')
    summary={}
    for condition in sorted({r['condition'] for r in rows}):
        selected=[r for r in rows if r['condition']==condition]
        summary[condition]={'successful':sum(r['success'] for r in selected),'runs':len(selected),
                            'execution_statuses':{s:sum(r['execution_status']==s for r in selected) for s in sorted({r['execution_status'] for r in selected})},
                            'critical_violations':sum(bool(r['critical_violations']) for r in selected),
                            'median_self_reported_unique_read_bytes':median_known(r['read_bytes'] for r in selected),
                            'median_self_reported_tool_calls':median_known(r['self_reported_tool_calls'] for r in selected),
                            'median_wall_seconds_upper_bound':median_known(r['wall_seconds_upper_bound'] for r in selected),
                            'wall_seconds_observed_runs':sum(r['wall_seconds_upper_bound'] is not None for r in selected),
                            'actual_token_usage':None,
                            'categories':{c:{'successful':sum(r['success'] for r in selected if r['category']==c),
                                             'runs':sum(r['category']==c for r in selected),
                                             'median_self_reported_unique_read_bytes':median_known(r['read_bytes'] for r in selected if r['category']==c)} for c in sorted({r['category'] for r in selected})}}
    by_task={}
    for task in sorted({r['task_id'] for r in rows}):
        by_task[task]={condition:{'successful':sum(r['success'] for r in rows if r['task_id']==task and r['condition']==condition),
                                  'runs':sum(r['task_id']==task and r['condition']==condition for r in rows)}
                       for condition in sorted({r['condition'] for r in rows if r['task_id']==task})}
    report={'summary':summary,'by_task':by_task,'rows':rows,
            'limitation':'AI semantic grades; literal quote checks only; repeated fixed tasks, not independent story samples'}
    write(output,report)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(dest='command',required=True)
    b=s.add_parser('blind'); b.add_argument('--runs',type=Path,required=True); b.add_argument('--output',type=Path,required=True)
    b=s.add_parser('summarize'); b.add_argument('--runs',type=Path,required=True); b.add_argument('--blind',type=Path,required=True); b.add_argument('--output',type=Path,required=True); b.add_argument('--adjudication',type=Path)
    a=p.parse_args()
    try:
        result=blind(a.runs,a.output) if a.command=='blind' else summarize(a.runs,a.blind,a.output,a.adjudication)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as e: p.exit(2,'ERROR: '+str(e)+'\n')

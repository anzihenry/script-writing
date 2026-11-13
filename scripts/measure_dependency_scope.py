#!/usr/bin/env python3
"""Prepare retained local changes and unanchored semantic scope review packets."""
import argparse
import importlib.util
import json
import shutil
from pathlib import Path

import harness_experiment as h

ROOT=Path(__file__).resolve().parents[1]
CASES=[
    ('appearance','bible','角色外观',[('灰外套固定','深蓝外套固定')]),
    ('knowledge','bible','人物知情',[('她当班前见过完整登记页，记得“三号、第四行”','她当班前未见过完整登记页，不知道编号和行号')]),
    ('world','bible','世界规则',[('不透明门','带透明观察窗的门'),('对方无法看到桌面，不知道她已比对纸片','对方能够看见桌面，知道她已比对纸片')]),
    ('wording','script_EP001','对白措辞',[('这钥匙，你在哪儿捡的？','钥匙，你在哪儿捡的？')]),
    ('foreshadow','outline','伏笔计划',[('F001：撕口关联在 EP002','F001：撕口关联在 EP003'),('"payoff": "EP002"','"payoff": "EP003"')]),
    ('end_state','script_EP001','前集末状态',[('钥匙在林夏右手；登记簿和纸片在桌面。','钥匙留在托盘里；林夏双手空着；登记簿和纸片在桌面。')]),
]


def prepare(output):
    output=Path(output).resolve()
    if output.exists():raise ValueError('scope study exists')
    output.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('scope_pipeline',ROOT/'skills/ai-short-drama-writing/scripts/pipeline.py')
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    measurements=[]
    for case_id,key,label,replacements in CASES:
        case=output/'reviews'/case_id;case.mkdir(parents=True)
        for name in ['before','after']:
            shutil.copytree(ROOT/'examples/return-season',case/name)
        root=case/'after';data=p.load(root);item=data['artifacts'][key]
        old=p.local(root,item['path']);text=old.read_text()
        for before,after in replacements:
            if text.count(before)!=1:raise ValueError('change anchor missing/ambiguous: '+before)
            text=text.replace(before,after)
        text=text.replace('v1.0','v1.1',1)
        path=old.with_name(old.stem+'-scope-v1.1'+old.suffix)
        path.write_text(text)
        p.register(root,key,item['kind'],item['scope'],path.relative_to(root).as_posix(),'v1.1')
        report=p.impact(root,key)
        measurements.append({'case_id':case_id,'category':label,'source':key,'file_affected':len(report['order']),
                             'stale_artifacts':sum(bool(row['errors']) for row in report['order']),
                             'candidate_location_count':sum(len(row['candidate_locations']) for row in report['order']),
                             'impact':report})
        h.write(case/'task.json',{'case_id':case_id,'category':label,'source':key,
                                 'artifacts':sorted(data['artifacts']),
                                 'old_source':item['path'],'new_source':path.relative_to(root).as_posix()})
        (case/'request.md').write_text('''你是独立语义复核范围评阅者。只读取本目录的task.json、before/和after/，不访问父目录/仓库/其他评阅结果，不启动代理，不修改项目。before是已知示例原件；after只将指定来源作局部新版本登记，下游保持旧字节和依赖。\n基于真实前后内容，判断task.artifacts每个产物在本次变更后是否需要针对性的语义/文本复核，给出关键场次和逐字来源。不要自动把所有传递依赖等同剧情变化，也不要假定某个尚未执行的修复已完成。新源与旧下游冲突必须指出；范围不确定时用uncertain。\n分类仅用于阅读优先级，不替代文件级STALE、版本/依赖再登记和gate；no_direct_semantic_change绝不是免检或批准。不要估算自己没测量的时间节省。\n写assessment.json：{"case_id":"...","items":[{"artifact_id":"...","decision":"review|no_direct_semantic_change|uncertain","locations":["实际场次/对白或文档章节"],"evidence":[{"path":"before或after内相对文件路径","quote":"连续逐字原文"}],"reason":"说明该变更的直接语义关系、无直接变化证据或不确定性"}],"critical_locations":[{"artifact_id":"...","location":"...","reason":"关键必须复核的实际内容"}],"limitations":[]}。每个artifact恰好一项。review/uncertain至少一条可核对的来源引用；no_direct也需说明依据，不能仅凭文件哈希相同断言无影响。无唯一改写答案，不实际改写正文。\n''')
    h.write(output/'measurements.json',{'cases':measurements,'limitation':'File-level impact measured; actual semantic scope awaits independent assessment; no state waived'})
    h.write(output/'input-hashes.json',h.files(output/'reviews'))
    return {'cases':len(measurements),'root':str(output)}


def verify_review(case):
    """Check delivery and literal evidence only; never assign semantic judgments."""
    case=Path(case).resolve()
    frozen=json.loads((case.parent.parent/'input-hashes.json').read_text())
    prefix=case.name+'/'
    expected={name[len(prefix):]:digest for name,digest in frozen.items() if name.startswith(prefix)}
    if not expected:raise ValueError('case not in frozen inputs')
    observed={name:digest for name,digest in h.files(case).items()
              if name in {'request.md','task.json'} or name.startswith(('before/','after/'))}
    if observed!=expected:raise ValueError('review input changed')
    task=json.loads((case/'task.json').read_text())
    assessment=json.loads((case/'assessment.json').read_text())
    if assessment.get('case_id')!=task['case_id']:raise ValueError('case identity mismatch')
    items=assessment['items'];ids=[row['artifact_id'] for row in items]
    if sorted(ids)!=sorted(task['artifacts']):raise ValueError('artifact inventory mismatch')
    counts={key:0 for key in ['review','no_direct_semantic_change','uncertain']}
    for row in items:
        decision=row['decision']
        if decision not in counts:raise ValueError('invalid decision')
        counts[decision]+=1
        if not isinstance(row.get('reason'),str) or not row['reason'].strip():raise ValueError('missing reason')
        if not isinstance(row.get('locations'),list):raise ValueError('missing locations')
        evidence=row.get('evidence')
        if not isinstance(evidence,list) or (decision!='no_direct_semantic_change' and not evidence):
            raise ValueError('missing source evidence')
        for item in evidence:
            name=item['path'];path=Path(name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] not in {'before','after'}:
                raise ValueError('evidence outside allowed sources')
            if name not in expected:raise ValueError('evidence not a frozen source')
            quote=item['quote']
            if not isinstance(quote,str) or not quote or quote not in (case/path).read_text():
                raise ValueError('nonliteral source quote')
    for row in assessment['critical_locations']:
        if row['artifact_id'] not in ids or not row['location'] or not row['reason']:
            raise ValueError('invalid critical location')
    if not isinstance(assessment['limitations'],list):raise ValueError('missing limitations')
    return {'case_id':task['case_id'],'assessment_sha256':h.sha(case/'assessment.json'),
            'artifacts':len(ids),'decisions':counts,
            'limitation':'Structure and literal evidence checked; semantic correctness requires independent assessment'}


def summarize(output):
    """Compare artifact sets, not semantic coverage of individual locations."""
    output=Path(output);rows=[]
    for measured in json.loads((output/'measurements.json').read_text())['cases']:
        case=output/'reviews'/measured['case_id'];verified=verify_review(case)
        assessment=json.loads((case/'assessment.json').read_text())
        impact={row['id']:row for row in measured['impact']['order']}
        priority={row['artifact_id'] for row in assessment['items'] if row['decision']!='no_direct_semantic_change'}
        no_direct={row['artifact_id'] for row in assessment['items'] if row['decision']=='no_direct_semantic_change'}
        critical={row['artifact_id'] for row in assessment['critical_locations']}
        rows.append({**verified,'file_affected':measured['file_affected'],
                     'stale_artifacts':measured['stale_artifacts'],
                     'candidate_location_count':measured['candidate_location_count'],
                     'priority_artifacts':sorted(priority),
                     'priority_outside_file_closure':sorted(priority-set(impact)),
                     'file_closure_without_direct_semantic_change':sorted(set(impact)&no_direct),
                     'critical_artifacts_without_candidate_locations':sorted(
                         key for key in critical if not impact.get(key,{}).get('candidate_locations'))})
    return {'cases':rows,'limitation':'Independent AI assessments of six fixed fixtures; artifact counts are not measured reading/time savings. Candidate location presence does not prove semantic coverage. All STALE and gate requirements remain authoritative.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output',type=Path)
    mode.add_argument('--verify-review',type=Path)
    mode.add_argument('--summarize',type=Path)
    args=parser.parse_args()
    result=summarize(args.summarize) if args.summarize else verify_review(args.verify_review) if args.verify_review else prepare(args.output)
    print(json.dumps(result,ensure_ascii=False,indent=2))

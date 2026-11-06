#!/usr/bin/env python3
"""Reconstruct M2 inputs from the frozen preparer; verify delivered evidence.

Checks only existing runs. A partial matrix or valid file hashes are not a
semantic pass. Does not execute models or overwrite any run.
"""
import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVAL=ROOT/'docs/validation/v0.3.0/experiments'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def verify(runs):
    frozen=EVAL/'frozen'
    spec=importlib.util.spec_from_file_location('frozen_preparer',frozen/'preparer.py')
    prep=importlib.util.module_from_spec(spec); spec.loader.exec_module(prep)
    prep.ROOT,prep.EVAL,prep.BANK=ROOT,EVAL,frozen/'bank'
    prep.verify_freeze()
    tasks=[t['case_id'] for t in read(frozen/'bank/tasks.json')['tasks'] if t['split']=='dev']
    scheduled={f'{task}-{condition}-r{replicate}' for task in tasks for condition in 'ABC' for replicate in (1,2)}
    rows=[]
    for run in sorted(Path(runs).iterdir()):
        if not run.is_dir() or not (run/'result.json').exists(): continue
        if run.name not in scheduled: raise ValueError('unexpected run: '+run.name)
        task,condition,replicate=run.name.split('-'); replicate=int(replicate[1:])
        manifest=read(run/'manifest.json'); result=read(run/'result.json')
        if (manifest['task_id'],manifest['condition'],manifest['replicate'])!=(task,condition,replicate):
            raise ValueError('schedule identity mismatch: '+run.name)
        if (result['task_id'],result['condition'],result['replicate'])!=(task,condition,replicate):
            raise ValueError('result identity mismatch: '+run.name)
        with tempfile.TemporaryDirectory() as tmp:
            expected=prep.prepare(task,condition,replicate,Path(tmp)/'run')
        if manifest['input_hashes']!=expected['input_hashes'] or manifest['request_sha256']!=expected['request_sha256']:
            raise ValueError('manifest differs from frozen preparation: '+run.name)
        if sha(run/'manifest.json')!=result['manifest_sha256']: raise ValueError('manifest changed: '+run.name)
        actual={}
        for name in expected['input_hashes']:
            path=run/'input'/name
            if not path.exists() and name.startswith('skills/'):
                path=frozen/'rules'/name
            if path.is_file(): actual[name]=sha(path)
        for path in (run/'input').rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                actual[path.relative_to(run/'input').as_posix()]=sha(path)
        if actual!=result.get('actual_input_hashes',manifest['input_hashes']):
            raise ValueError('input evidence changed: '+run.name)
        request=sha(run/'request.md') if (run/'request.md').is_file() else None
        if request!=result.get('actual_request_sha256',manifest['request_sha256']):
            raise ValueError('request evidence changed: '+run.name)
        unchanged=actual==expected['input_hashes'] and request==expected['request_sha256']
        if unchanged!=result['input_unchanged']: raise ValueError('incorrect input status: '+run.name)
        for name,digest in result['output_hashes'].items():
            if sha(run/'output'/name)!=digest: raise ValueError('output evidence changed: '+run.name)
        rows.append({'run_id':run.name,'input_matches_frozen':unchanged,'record_status':result['status']})
    return {'verified_runs':len(rows),'expected_runs':len(scheduled),'matrix_complete':len(rows)==len(scheduled),
            'rows':rows,'semantic_grading':'Not inferred from evidence integrity'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('runs',type=Path); p.add_argument('--output',type=Path); a=p.parse_args()
    try:
        report=verify(a.runs)
        if a.output:
            if a.output.exists(): raise ValueError('report output already exists')
            a.output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
    except (ValueError,OSError,KeyError,TypeError) as e: p.exit(2,str(e)+'\n')

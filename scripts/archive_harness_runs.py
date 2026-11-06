#!/usr/bin/env python3
"""Append completed runs to durable evidence; shared skill bytes live in freeze."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'docs/validation/v0.3.0/experiments/frozen'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def archive(source, destination):
    source,destination=Path(source),Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    if (source/'schedule.json').exists():
        schedule=json.loads((source/'schedule.json').read_text())
        portable={'runs':[{'run_id':x['run_id']} for x in schedule['runs']],
                  'policy':schedule.get('policy'),'original_schedule_sha256':sha(source/'schedule.json')}
        target=destination/'schedule.json'
        encoded=json.dumps(portable,indent=2)+'\n'
        if target.exists() and target.read_text()!=encoded:
            raise ValueError('schedule changed')
        if not target.exists(): target.write_text(encoded)
    added=[]
    for run in sorted(source.iterdir()):
        if not run.is_dir() or not (run/'result.json').exists(): continue
        target=destination/run.name
        manifest=json.loads((run/'manifest.json').read_text())
        result=json.loads((run/'result.json').read_text())
        if sha(run/'manifest.json')!=result['manifest_sha256']: raise ValueError('manifest changed')
        request_hash=sha(run/'request.md') if (run/'request.md').is_file() else None
        if request_hash!=result.get('actual_request_sha256',manifest['request_sha256']):
            raise ValueError('request changed after finalization')
        observed={p.relative_to(run/'input').as_posix():sha(p) for p in (run/'input').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        expected=result.get('actual_input_hashes',manifest['input_hashes'])
        if observed!=expected: raise ValueError('input changed after finalization: '+run.name)
        shared=set()
        for name,digest in observed.items():
            if name.startswith('skills/') and (FROZEN/'rules'/name).is_file() and sha(FROZEN/'rules'/name)==digest:
                shared.add(name)
        for name,digest in result['output_hashes'].items():
            if sha(run/'output'/name)!=digest: raise ValueError('output changed: '+name)
        if target.exists():
            if sha(target/'result.json')!=sha(run/'result.json'): raise ValueError('existing archive differs: '+run.name)
            for name,digest in result['output_hashes'].items():
                if sha(target/'output'/name)!=digest: raise ValueError('archived output changed: '+name)
            continue
        with tempfile.TemporaryDirectory(dir=destination) as tmp:
            staging=Path(tmp)/run.name; staging.mkdir()
            for name in ['request.md','manifest.json','result.json']:
                if (run/name).exists(): shutil.copyfile(run/name,staging/name)
            for name in ['output','attempts']:
                if (run/name).exists(): shutil.copytree(run/name,staging/name)
            (staging/'input').mkdir()
            for name in observed:
                if name in shared: continue
                dest=staging/'input'/name; dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(run/'input'/name,dest)
            (staging/'archive.json').write_text(json.dumps({'observed_input_hashes':observed,'shared_frozen_rules':sorted(shared),
                                                         'observed_request_sha256':request_hash,
                                                         'note':'Input mutations, if present at finalization, are preserved as failure evidence.'},indent=2)+'\n')
            staging.rename(target)
        added.append(run.name)
    return {'added':added,'archived':len(list(destination.glob('*/result.json'))),
            'shared_rules':'experiments/frozen/rules; validate each run manifest input_hashes'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('source',type=Path); p.add_argument('destination',type=Path); a=p.parse_args()
    try: print(json.dumps(archive(a.source,a.destination),indent=2))
    except (ValueError,OSError,KeyError) as e: p.exit(2,str(e)+'\n')

#!/usr/bin/env python3
"""Reproduce v0.3 observations in temporary copies; no model quality claims."""
import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location('pipeline', ROOT / 'skills/ai-short-drama-writing/scripts/pipeline.py')
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    freeze = json.loads((ROOT / 'docs/validation/v0.2.1/semantic/freeze.json').read_text())
    rule = 'skills/ai-short-drama-continuity-audit/SKILL.md'
    before = (ROOT / rule).read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        changed = Path(tmp) / 'rule.md'
        changed.write_bytes(before + b'\n<!-- baseline-only mutation -->\n')
        coupling = {'path': rule, 'original_matches_freeze': hashlib.sha256(before).hexdigest() == freeze['files'][rule],
                    'changed_matches_freeze': p.sha(changed) == freeze['files'][rule],
                    'historical_guard': 'tests/test_semantic_protocol.py:test_frozen_inputs_and_answer_coverage'}
        root = Path(tmp) / 'project'
        shutil.copytree(ROOT / 'examples/return-season', root)
        p.append_episodes(root, 4)
        task = p.next_steps(root, 'EP004')['next']
        data = p.load(root)
        inputs = [{'id': x['id'], 'path': data['artifacts'][x['id']]['path'],
                   'revision': data['artifacts'][x['id']]['revision']} for x in task['inputs'] if x['id']]
        recovery = {'next': task, 'additional_manifest_lookups': inputs,
                    'not_in_next': ['input file paths and hashes', 'rule reading set', 'source excerpts', 'completion commands']}
        script = root / 'episodes/EP001-v1.0.md'
        old = script.read_text()
        new = old.replace('这钥匙，你在哪儿捡的？', '钥匙在哪儿捡的？')
        assert old != new
        script.write_text(new)
        checks = p.inspect(root, p.load(root))
        affected = [k for k, errors in checks.items() if errors]
        impact = {'change': 'EP001-D006: delete redundant demonstrative; no event or state change',
                  'stale_artifacts': affected, 'stale_count': len(affected),
                  'downstream_count': len(affected) - 1,
                  'classification': 'Conservative file-level revalidation, not an incorrect gate result'}
    print(json.dumps({'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                      'python': platform.python_version(), 'platform': platform.platform(),
                      'coupling': coupling, 'recovery': recovery, 'impact': impact}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Prepare an oracle-free input directory; does not launch agents or models."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path('docs/validation/v0.3.0/archive/v0.2.1')
PUBLIC = 'tests/fixtures/semantic-long-range/cases.json'
RULES = [
    'skills/ai-short-drama-continuity-audit/SKILL.md',
    'skills/ai-short-drama-story-audit/SKILL.md',
    'skills/ai-short-drama-writing/references/common.md',
    'skills/ai-short-drama-writing/references/standards.md',
    'skills/ai-short-drama-writing/references/workflow.md',
    'skills/ai-short-drama-writing/references/season-review.md',
    'skills/ai-short-drama-writing/references/structured-records.md',
    'skills/ai-short-drama-writing/assets/templates.md',
]


def archived_inputs():
    """Verify immutable snapshots against the original freeze, not working rules."""
    freeze = json.loads((ROOT / 'docs/validation/v0.2.1/semantic/freeze.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / ARCHIVE / 'manifest.json').read_text(encoding='utf-8'))
    if set(manifest['files']) != set(freeze['files']):
        raise ValueError('archive coverage differs from original freeze')
    for name, digest in freeze['files'].items():
        record = manifest['files'][name]
        if record['snapshot'] != 'files/' + name or record['sha256'] != digest:
            raise ValueError('archive mapping changed: ' + name)
        path = ROOT / ARCHIVE / 'files' / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('archived input changed/missing: ' + name)
    return ROOT / ARCHIVE / 'files', freeze


def rule_closure(names):
    """Collect local Markdown dependencies; external URLs are references only."""
    pending, seen = list(names), set()
    while pending:
        name = pending.pop()
        path = (ROOT / name).resolve()
        try:
            path.relative_to((ROOT / 'skills').resolve())
        except ValueError:
            raise ValueError('rule dependency outside skills: ' + str(name))
        relative = path.relative_to(ROOT.resolve()).as_posix()
        if relative in seen:
            continue
        if not path.is_file():
            raise ValueError('missing rule dependency: ' + relative)
        seen.add(relative)
        if path.suffix == '.md':
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if '://' in link or link.startswith('#'):
                    continue
                target = link.split('#')[0]
                pending.append(str(path.parent / target))
    return sorted(seen)


def prepare(destination, round_number, mode='historical', cases_path=None, rules=None):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('output already exists; refusing overwrite')
    if round_number not in (1, 2) or mode not in {'historical', 'current'}:
        raise ValueError('invalid round/mode')
    if mode == 'historical':
        if cases_path is not None or rules is not None:
            raise ValueError('historical mode does not accept current inputs')
        source_root, freeze = archived_inputs()
        source, selected = source_root / PUBLIC, RULES
    else:
        if cases_path is None or not rules:
            raise ValueError('current mode requires --cases and --rule')
        source_root = ROOT
        source = Path(cases_path)
        if source.name in {'oracle.json', 'outputs.json', 'grading.json'}:
            raise ValueError('cases must be public inputs, not answers or outputs')
        selected = rule_closure(rules)
    raw = source.read_bytes()
    payload = json.loads(raw)
    cases = payload.get('cases') if isinstance(payload, dict) else None
    if not isinstance(cases, list) or not cases or any(not isinstance(x, dict) or not isinstance(x.get('case_id'), str) or not x['case_id'].strip() for x in cases):
        raise ValueError('nonempty cases with case_id required')
    if len({x['case_id'] for x in cases}) != len(cases):
        raise ValueError('duplicate case_id')
    if round_number == 2:
        cases.reverse()
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp) / 'input'
        staging.mkdir()
        for name in selected:
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_root / name, target)
        (staging / 'cases.json').write_text(json.dumps({'cases': cases}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        manifest = {'round': round_number, 'order': [x['case_id'] for x in cases],
                    'source_sha256': hashlib.sha256(raw).hexdigest(), 'rules': selected,
                    'isolation': 'Prepared without oracle or other-round outputs; runner must use a fresh context.'}
        if mode == 'current':
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
            dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
            manifest.update(schema_version=1, mode=mode, source_path=str(source),
                            source_commit=commit, source_dirty=dirty,
                            entry_rules=list(rules),
                            files={p.relative_to(staging).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted(staging.rglob('*')) if p.is_file()})
        (staging / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        prompt = '''请在全新上下文执行本轮短剧审稿评测。只读取本目录 manifest.json 列出的规则文件和 cases.json，不读取仓库、oracle、其他轮输出或历史聊天。不启动其他代理，不修改输入，不改写剧本。
按 manifest.order 顺序审读全部案例。每例使用连续性和叙事审核技能，回答 fact_questions，报告有依据的问题。不要为了凑数找问题，也不要假定所有案例有错。超出已给范围的质量维度标未验证。
输出一个 JSON 对象到 outputs.json，结构为 {"cases":[{"case_id":"C01","findings":[{"severity":"P1","summary":"...","evidence":[{"location":"EP001-SC001","quote":"逐字原文"}],"minimum_fix":"...","affected_range":["EP001"]}],"facts":[{"question":"与输入完全相同","answer":"...","evidence":[{"location":"EP001-SC001","quote":"逐字原文"}]}],"limitations":["..."]}]}。
每条 finding/fact 必须有实际来源证据；quote 是对应 location 小节中连续的原文片段。无问题时 findings=[]。禁止把人物谎言、观众所知、闪回、未到期伏笔自动当成当前事实或错误。不声明真人批准、模型族独立性、真实下游接收。完成后报告实际读取范围及输出位置。
'''
        (staging / 'request.md').write_text(prompt, encoding='utf-8')
        if mode == 'current':
            prompt = prompt.replace('manifest.json 列出的规则文件和 cases.json',
                                    'cases.json 与 manifest.entry_rules 入口，其他 manifest.rules 文件仅按任务需要读取')
            (staging / 'request.md').write_text(prompt, encoding='utf-8')
            manifest['files']['request.md'] = hashlib.sha256((staging / 'request.md').read_bytes()).hexdigest()
            (staging / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        staging.rename(destination)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', type=int, choices=[1, 2], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['historical', 'current'], default='historical')
    parser.add_argument('--cases', type=Path)
    parser.add_argument('--rule', action='append', dest='rules')
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.output, args.round, args.mode, args.cases, args.rules), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(2, 'ERROR: ' + str(error) + '\n')

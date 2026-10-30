#!/usr/bin/env python3
"""Prepare an oracle-free input directory; does not launch agents or models."""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


def prepare(destination, round_number):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('output already exists; refusing overwrite')
    freeze = json.loads((ROOT / 'docs/validation/v0.2.1/semantic/freeze.json').read_text(encoding='utf-8'))
    for name in [PUBLIC] + RULES:
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != freeze['files'][name]:
            raise ValueError('frozen input changed: ' + name)
    cases = json.loads((ROOT / PUBLIC).read_text(encoding='utf-8'))['cases']
    if round_number == 2:
        cases.reverse()
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp) / 'input'
        staging.mkdir()
        for name in RULES:
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        (staging / 'cases.json').write_text(json.dumps({'cases': cases}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        manifest = {'round': round_number, 'order': [x['case_id'] for x in cases],
                    'source_sha256': freeze['files'][PUBLIC], 'rules': RULES,
                    'isolation': 'Prepared without oracle or other-round outputs; runner must use a fresh context.'}
        (staging / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        prompt = '''请在全新上下文执行本轮短剧审稿评测。只读取本目录 manifest.json 列出的规则文件和 cases.json，不读取仓库、oracle、其他轮输出或历史聊天。不启动其他代理，不修改输入，不改写剧本。
按 manifest.order 顺序审读全部案例。每例使用连续性和叙事审核技能，回答 fact_questions，报告有依据的问题。不要为了凑数找问题，也不要假定所有案例有错。超出已给范围的质量维度标未验证。
输出一个 JSON 对象到 outputs.json，结构为 {"cases":[{"case_id":"C01","findings":[{"severity":"P1","summary":"...","evidence":[{"location":"EP001-SC001","quote":"逐字原文"}],"minimum_fix":"...","affected_range":["EP001"]}],"facts":[{"question":"与输入完全相同","answer":"...","evidence":[{"location":"EP001-SC001","quote":"逐字原文"}]}],"limitations":["..."]}]}。
每条 finding/fact 必须有实际来源证据；quote 是对应 location 小节中连续的原文片段。无问题时 findings=[]。禁止把人物谎言、观众所知、闪回、未到期伏笔自动当成当前事实或错误。不声明真人批准、模型族独立性、真实下游接收。完成后报告实际读取范围及输出位置。
'''
        (staging / 'request.md').write_text(prompt, encoding='utf-8')
        staging.rename(destination)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', type=int, choices=[1, 2], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output, args.round), ensure_ascii=False, indent=2))

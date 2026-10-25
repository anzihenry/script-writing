import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_pipeline import p, ROOT


class AcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'season'
        shutil.copytree(ROOT / 'examples/return-season', self.root)

    def test_three_episode_baseline_and_cli(self):
        self.assertEqual(p.continuity_index(self.root)['status'], 'RECORDED')
        self.assertTrue(p.review_check(self.root, 'reviews/season-v1.0.md')['full_season'])
        for ep in p.load(self.root)['episodes']:
            self.assertEqual(p.parity(self.root, ep)['status'], 'MATCH')
            self.assertFalse(p.gate(self.root, p.load(self.root), 'G5', ep)[0])
        result = subprocess.run([sys.executable, str(p.HOME / 'scripts/pipeline.py'), 'next', str(self.root), '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'STRUCTURE_READY')

    def test_legacy_resume_without_rewriting_baseline(self):
        legacy = Path(self.temp.name) / 'legacy'
        shutil.copytree(ROOT / 'examples/return-demo', legacy)
        before = p.load(legacy)
        hashes = {k: p.sha(legacy / x['path']) for k, x in before['artifacts'].items()}
        p.append_episodes(legacy, 3)
        self.assertEqual(p.load(legacy)['artifacts'], before['artifacts'])
        self.assertEqual({k: p.sha(legacy / x['path']) for k, x in before['artifacts'].items()}, hashes)
        self.assertEqual(p.next_steps(legacy)['next']['scope'], 'EP002')
        self.assertEqual(p.parity(legacy, 'EP001')['status'], 'UNVERIFIED')
        self.assertEqual(p.continuity_index(legacy)['status'], 'UNVERIFIED')

    def test_feedback_revision_revalidation_delivery_roundtrip(self):
        first, second = Path(self.temp.name) / 'old.zip', Path(self.temp.name) / 'new.zip'
        p.bundle(self.root, 'EP001', first, 'SIM-PKG1')
        original_hash = p.sha(first)
        p.issue_action(self.root, 'add', 'SIM-Q1', 'EP001', 'P1', 'EP001-D006', '模拟：来源问题需要更简洁', ['script_EP001'])
        p.feedback_action(self.root, 'add', 'SIM-F1', 'SIM-PKG1', '模拟接收方', 'EP001-D006', '模拟反馈，不代表真实接收', 'script', ['SIM-Q1'])
        # A wording-only revision with retained old files and explicit downstream revalidation.
        script = self.root / 'episodes/EP001-v1.0.md'
        changed = script.read_text().replace('这钥匙，你在哪儿捡的？', '钥匙在哪儿捡的？')
        (self.root / 'episodes/EP001-v1.1.md').write_text(changed)
        p.register(self.root, 'script_EP001', 'script', 'EP001', 'episodes/EP001-v1.1.md', 'v1.1')
        self.assertEqual(p.continuity_index(self.root)['status'], 'UNVERIFIED')
        self.assertTrue(p.gate(self.root, p.load(self.root), 'G5', 'EP003')[0])
        report = p.impact(self.root, 'script_EP001')
        self.assertIn('script_EP003', [r['id'] for r in report['order']])
        for row in report['order']:
            key = row['id']
            item = p.load(self.root)['artifacts'][key]
            if key == 'script_EP001':
                continue
            old = self.root / item['path']
            path = item['path'].replace('v1.0', 'v1.1')
            content = old.read_text().replace('v1.0', 'v1.1').replace('这钥匙，你在哪儿捡的？', '钥匙在哪儿捡的？')
            if item['kind'] == 'export':
                payload = json.loads(content)
                payload['bible_revision'] = 'v1.0'
                content = json.dumps(payload, ensure_ascii=False, indent=2)
            (self.root / path).write_text(content)
            p.register(self.root, key, item['kind'], item['scope'], path, 'v1.1', item['status'], item['evidence'],
                       '模拟演练实际比对：仅 EP001-D006 删去冗余指示词；事件、持物、知情及后集行为不变。')
            if item['kind'] == 'review' and item['scope'] == 'EP001':
                p.register(self.root, 'script_EP001', 'script', 'EP001', 'episodes/EP001-v1.1.md', 'v1.1', 'reviewed', '模拟演练作者复核：reviews/EP001-v1.1.md')
                p.issue_action(self.root, 'resolve', 'SIM-Q1', evidence='模拟：新旧台词比对；对白问题修复，语义和状态不变')
        self.assertEqual(p.continuity_index(self.root)['status'], 'RECORDED')
        self.assertEqual(p.parity(self.root, 'EP001')['status'], 'MATCH')
        p.bundle(self.root, 'EP001', second, 'SIM-PKG2', 'SIM-PKG1')
        p.feedback_action(self.root, 'update', 'SIM-F1', status='closed', verification='模拟：对 SIM-PKG2 的字段核对与回验，不代表真实接收')
        p.receipt(self.root, 'SIM-PKG2', 'accepted', '模拟接收记录，不代表真实接收')
        result = p.measure(self.root, 'SIM-T1', 'SIM-PKG2', 63, '合成测试数值', '仅验证差值计算，不是实测')
        self.assertEqual(result['delta_seconds'], 3)
        self.assertEqual(p.sha(first), original_hash)
        self.assertTrue(script.exists())
        self.assertFalse(any(p.inspect(self.root, p.load(self.root)).values()))
        p.issue_action(self.root, 'reopen', 'SIM-Q1')
        self.assertEqual(p.feedback_action(self.root, 'list')[0]['status'], 'awaiting_verification')
        self.assertIsNone(p.feedback_action(self.root, 'list')[0]['verification'])

    def test_malformed_extensions_rejected_without_traceback(self):
        data = p.load(self.root)
        data['deliveries'] = [{'id': 'broken'}]
        (self.root / 'project.json').write_text(json.dumps(data))
        result = subprocess.run([sys.executable, str(p.HOME / 'scripts/pipeline.py'), 'next', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def test_skill_names_metadata_and_local_links(self):
        skills = list((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertEqual(len(skills), 37)
        for skill in skills:
            text = skill.read_text()
            self.assertIn('name: ' + skill.parent.name, text)
            self.assertTrue((skill.parent / 'agents/openai.yaml').is_file())
        for doc in (ROOT / 'skills').rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
                if '://' not in link and not link.startswith('#'):
                    target = link.split('#')[0]
                    self.assertTrue((doc.parent / target).exists(), f'{doc}: {target}')

    def test_season_review_does_not_ignore_open_major_issues(self):
        p.issue_action(self.root, 'add', 'BLOCK', 'EP002', 'P1', 'EP002-SC001', 'Test blocking issue', ['script_EP002'])
        result = p.review_check(self.root, 'reviews/season-v1.0.md')
        self.assertEqual(result['status'], 'NEEDS_WORK')
        self.assertIn('BLOCK', result['blocking_issues'])
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'season_review', 'season_review', 'project', 'reviews/season-v1.0.md', 'v1.0', 'reviewed', 'Cannot override blocker')

    def test_stale_season_report_cannot_reuse_current_sources(self):
        p.register(self.root, 'script_EP003', 'script', 'EP003', 'episodes/EP003-v1.0.md', 'v1.1')
        p.register(self.root, 'continuity_EP003', 'continuity', 'EP003', 'continuity/EP003-v1.0.md', 'v1.1', note='Test revalidation against unchanged content')
        checks = p.inspect(self.root, p.load(self.root))
        self.assertFalse(checks['script_EP003'])
        self.assertFalse(checks['continuity_EP003'])
        self.assertTrue(checks['season_review'])
        with self.assertRaises(p.Invalid): p.review_check(self.root, 'reviews/season-v1.0.md')

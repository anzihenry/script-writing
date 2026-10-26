"""Replay immutable acceptance artifacts; semantic judgments remain in signed-off reports."""
import hashlib
import json
import unittest
import zipfile
from pathlib import Path
from test_pipeline import p, ROOT

EVIDENCE = ROOT / 'docs/validation/v0.2.0-final'


class MilestoneEvidenceTest(unittest.TestCase):
    def test_substantive_revision_preserves_source_and_packages(self):
        root = EVIDENCE / 'revision'
        preserved = json.loads((root / 'preserved-v1.0.json').read_text())
        for name, record in preserved.items():
            self.assertEqual(p.sha(root / record['copy_path']), record['source_sha256'], name)
            self.assertEqual(p.sha(ROOT / 'examples/return-season' / name), record['source_sha256'], name)
        summary = json.loads((root / 'summary.json').read_text())
        self.assertEqual(p.sha(root / 'project/project.json'), summary['project_json_sha256'])
        self.assertEqual(len(summary['package_sha256']), 6)
        for name, digest in summary['package_sha256'].items():
            archive_path = root / 'packages' / name
            self.assertEqual(p.sha(archive_path), digest)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIsNone(archive.testzip())
                manifest = json.loads(archive.read('delivery-manifest.json'))
                for item in manifest['files'].values():
                    content = archive.read(item['path'])
                    self.assertEqual(hashlib.sha256(content).hexdigest(), item['sha256'])
                    self.assertEqual(content, (root / 'project' / item['path']).read_bytes())

    def test_substantive_revision_current_chain_and_real_dialogue_change(self):
        root = EVIDENCE / 'revision/project'
        data = p.load(root)
        self.assertFalse(any(p.inspect(root, data).values()))
        self.assertEqual(p.continuity_index(root)['status'], 'RECORDED')
        for ep in data['episodes']:
            self.assertFalse(p.gate(root, data, 'G5', ep)[0])
            self.assertEqual(p.parity(root, ep)['status'], 'MATCH')
        old = p.embedded(root, {'path': 'episodes/EP002-v1.0.md'}, 'script-json')
        new = p.embedded(root, {'path': 'episodes/EP002-v2.0.md'}, 'script-json')
        old_lines = {x['id']: x['text'] for s in old['scenes'] for x in s['dialogue']}
        new_lines = {x['id']: x['text'] for s in new['scenes'] for x in s['dialogue']}
        # This is a material dialogue rewrite, not merely a revision-label refresh.
        self.assertEqual(set(old_lines), set(new_lines))
        self.assertGreaterEqual(sum(old_lines[k] != new_lines[k] for k in old_lines), 4)
        issue = next(x for x in data['issues'] if x['id'] == 'Q-NEW-001')
        self.assertEqual(issue['status'], 'resolved')
        self.assertTrue(all(v == 'v2.0' for v in issue['verified_revisions'].values()))
        self.assertEqual(next(x for x in data['feedback'] if x['id'] == 'FB-SIM-001')['status'], 'closed')
        newer = [x for x in data['deliveries'] if x['supersedes']]
        self.assertEqual(len(newer), 3)
        self.assertTrue(all(x['status'] == 'accepted' and '模拟' in x['evidence'] for x in newer))

"""Replay immutable acceptance artifacts; semantic judgments remain in separate review reports."""
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

    def test_two_round_grading_is_bound_to_raw_outputs(self):
        oracle_path = EVIDENCE / 'oracle.json'
        oracle = json.loads(oracle_path.read_text())
        expected = {x['case_id']: x for x in oracle['cases']}
        for round_name in ['round-1', 'round-2']:
            output_path = EVIDENCE / 'runs' / round_name / 'outputs.json'
            outputs = {x['case_id']: x for x in json.loads(output_path.read_text())}
            grade = json.loads((EVIDENCE / 'grading' / (round_name + '.json')).read_text())
            self.assertEqual(grade['oracle_sha256'], p.sha(oracle_path))
            self.assertEqual(grade['outputs_sha256'], p.sha(output_path))
            self.assertEqual(set(outputs), set(expected))
            self.assertEqual({x['case_id'] for x in grade['cases']}, set(expected))
            for row in grade['cases']:
                out, source = outputs[row['case_id']], expected[row['case_id']]
                if source['kind'] == 'negative':
                    self.assertFalse([x for x in out['findings'] if x['severity'] in {'P0', 'P1'}])
                self.assertEqual(len(row['matched_finding_indices']), len(source['expected_findings']))
                for i in row['matched_finding_indices']:
                    self.assertIn(out['findings'][i]['severity'], ['P0', 'P1'])
                    self.assertTrue(out['findings'][i]['evidence'])
                self.assertEqual([x['oracle_fact_index'] for x in row['required_facts']], list(range(len(source['required_state_facts']))))
                for fact in row['required_facts']:
                    self.assertTrue(fact['support'])
                    for support in fact['support']:
                        self.assertEqual(support['value'], out['facts'][support['index']]['value'])
                        self.assertEqual(support['location'], out['facts'][support['index']]['location'])
                self.assertEqual(row['result'], 'PASS')

    def test_independent_review_and_official_validation_are_present(self):
        review = json.loads((EVIDENCE / 'revision-independent-review.json').read_text())
        self.assertEqual(review['unresolved_p0'], 0)
        self.assertEqual(review['unresolved_p1'], 0)
        self.assertFalse(review['unresolved_blocking_or_major'])
        official = json.loads((EVIDENCE / 'official-skill-validation.json').read_text())
        self.assertEqual({x['skill'] for x in official['results']}, {x.parent.name for x in (ROOT / 'skills').glob('*/SKILL.md')})
        self.assertTrue(all(x['exit_code'] == 0 for x in official['results']))

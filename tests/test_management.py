import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import test_pipeline as baseline
p = baseline.p


class ManagementTest(unittest.TestCase):
    setUp = baseline.PipelineTest.setUp
    add = baseline.PipelineTest.add
    chain = baseline.PipelineTest.chain
    def test_append_preserves_and_is_idempotent(self):
        self.chain()
        before = p.load(self.root)
        self.assertEqual(p.append_episodes(self.root, 3), ['EP003'])
        after = p.load(self.root)
        self.assertEqual(before['artifacts'], after['artifacts'])
        self.assertEqual(p.append_episodes(self.root, 3), [])
        self.assertEqual(after, p.load(self.root))

    def test_append_preflights_all_paths(self):
        target = self.root / 'handoff/EP003-v1.0.md'
        target.write_text('existing')
        before = p.load(self.root)
        with self.assertRaises(p.Invalid): p.append_episodes(self.root, 3)
        self.assertFalse((self.root / 'episodes/EP003-v1.0.md').exists())
        self.assertEqual(p.load(self.root), before)
        self.assertEqual(target.read_text(), 'existing')

    def test_issue_lifecycle_and_evidence(self):
        self.chain()
        p.issue_action(self.root, 'add', 'Q1', 'EP001', 'P0', 'SC1', 'Conflict', ['script_EP001'])
        with self.assertRaises(p.Invalid):
            p.issue_action(self.root, 'accept', 'Q1', evidence='accepted', actor='Producer')
        with self.assertRaises(p.Invalid): p.issue_action(self.root, 'resolve', 'Q1')
        p.issue_action(self.root, 'resolve', 'Q1', evidence='Checked actual source')
        self.assertFalse(p.gate(self.root, p.load(self.root), 'G5', 'EP001')[0])
        p.issue_action(self.root, 'reopen', 'Q1')
        self.assertTrue(p.gate(self.root, p.load(self.root), 'G5', 'EP001')[0])
        self.assertEqual(len(p.load(self.root)['events']), 3)

    def test_next_includes_prerequisite_episodes(self):
        self.chain()
        report = p.next_steps(self.root, 'EP002')
        self.assertEqual((report['next']['stage'], report['next']['scope']), ('G3', 'EP002'))
        (self.root / 'script_EP001-v1.0.md').write_text('changed')
        report = p.next_steps(self.root, 'EP002')
        self.assertEqual(report['next']['scope'], 'EP001')
        self.assertEqual(report['next']['stage'], 'G3')

    def test_checkpoint_does_not_hide_staleness(self):
        self.chain()
        p.checkpoint(self.root, 'B1', ['EP001'], 'Write EP002', 'EP001 ending')
        before = (self.root / 'project.json').read_bytes()
        self.assertEqual(p.next_steps(self.root)['changed_since_checkpoint'], [])
        (self.root / 'script_EP001-v1.0.md').write_text('changed')
        self.assertIn('script_EP001', p.next_steps(self.root)['changed_since_checkpoint'])
        self.assertEqual((self.root / 'project.json').read_bytes(), before)
        with self.assertRaises(p.Invalid):
            p.checkpoint(self.root, 'B1', ['EP001'], 'Again', 'Again')

    def test_impact_orders_and_does_not_clear_staleness(self):
        self.chain(); self.chain('EP002')
        (self.root / 'script_EP001-v1.0.md').write_text('changed')
        report = p.impact(self.root, 'script_EP001')
        ids = [x['id'] for x in report['order']]
        self.assertLess(ids.index('continuity_EP001'), ids.index('script_EP002'))
        self.assertNotIn('bible', ids)
        p.impact_note(self.root, 'script_EP001', 'script_EP002', 'reviewed_unchanged', 'Test review')
        self.assertTrue(p.inspect(self.root, p.load(self.root))['script_EP002'])

    def test_feedback_unknown_package_and_missing_verification(self):
        self.chain()
        p.feedback_action(self.root, 'add', 'F1', 'unknown', 'Test recipient', 'EP001-SC001', 'Test finding', 'production')
        with self.assertRaises(p.Invalid):
            p.feedback_action(self.root, 'update', 'F1', status='closed', verification='test')
        self.assertEqual(p.feedback_action(self.root, 'list')[0]['status'], 'triage')

    def test_append_rolls_back_if_manifest_write_fails(self):
        from unittest.mock import patch
        before = (self.root / 'project.json').read_bytes()
        with patch.object(p, 'save', side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError): p.append_episodes(self.root, 3)
        self.assertEqual((self.root / 'project.json').read_bytes(), before)
        self.assertFalse((self.root / 'episodes/EP003-v1.0.md').exists())

    def test_closed_issue_requires_reopen_before_new_revision(self):
        self.chain()
        p.issue_action(self.root, 'add', 'Q1', 'EP001', 'P1', 'SC1', 'Conflict', ['script_EP001'])
        p.issue_action(self.root, 'resolve', 'Q1', evidence='Test actual check')
        (self.root / 'new.md').write_text('changed content')
        before = (self.root / 'project.json').read_bytes()
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'script_EP001', 'script', 'EP001', 'new.md', 'v1.1')
        self.assertEqual((self.root / 'project.json').read_bytes(), before)
        p.issue_action(self.root, 'reopen', 'Q1')
        p.register(self.root, 'script_EP001', 'script', 'EP001', 'new.md', 'v1.1')

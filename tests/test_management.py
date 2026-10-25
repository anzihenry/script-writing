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

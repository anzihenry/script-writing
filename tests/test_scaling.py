import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import scale_fixture
import test_pipeline as baseline
p = baseline.p


class ScalingTest(unittest.TestCase):
    def test_scale_and_freshness_between_commands(self):
        for count in [3, 30, 100]:
            with self.subTest(episodes=count), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'project'
                data = scale_fixture.build(root, count)
                for command in ['next', 'status']:
                    with contextlib.redirect_stdout(io.StringIO()), patch.object(p, 'inspect', wraps=p.inspect) as checks, patch.object(p, 'sha', wraps=p.sha) as hashes:
                        self.assertEqual(p.main([command, str(root)]), 0)
                    self.assertEqual(checks.call_count, 1)
                    self.assertEqual(hashes.call_count, len(data['artifacts']))
                self.assertEqual(p.next_steps(root)['status'], 'STRUCTURE_READY')
                (root / 'script_EP001.md').write_text('Changed after previous command')
                report = p.next_steps(root)
                self.assertEqual(report['next']['scope'], 'EP001')
                self.assertIn('handoff_EP' + str(count).zfill(3), report['artifact_errors'])

    def test_shared_and_direct_gate_results_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'project'
            data = scale_fixture.build(root, 3)
            (root / 'script_EP002.md').unlink()
            checks, lookup = p.inspect(root, data), p.artifact_index(data)
            for ep in data['episodes']:
                for stage in ['G3', 'G4', 'G5']:
                    self.assertEqual(p.gate(root, data, stage, ep), p.gate(root, data, stage, ep, checks, lookup))

    def test_duplicate_locked_history_hashes_once(self):
        case = baseline.PipelineTest()
        case.setUp()
        try:
            case.add('brief', status='locked')
            case.add('brief', revision='v2')
            data = p.load(case.root)
            data['history'].append(data['history'][-1])
            with patch.object(p, 'sha', wraps=p.sha) as hashes:
                self.assertFalse(any(p.inspect(case.root, data).values()))
            self.assertEqual(hashes.call_count, 2)
            (case.root / 'brief-v1.0.md').write_text('Changed locked baseline')
            self.assertTrue(p.inspect(case.root, data)['brief'])
        finally:
            case.doCleanups()

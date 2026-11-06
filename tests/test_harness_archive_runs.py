import tempfile
import unittest
from pathlib import Path
from test_semantic_protocol import module


class HarnessRunArchiveTest(unittest.TestCase):
    def test_failed_run_preserves_mutated_input_and_rejects_later_change(self):
        runner=module('harness_experiment'); archiver=module('archive_harness_runs')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); runs=root/'runs'; runs.mkdir(); run=runs/'one'
            runner.prepare('R01','A',1,run,pilot=True)
            (run/'input/source.md').write_text('Wrongly modified by executor')
            (run/'output/answer.md').write_text('Synthetic failure output')
            runner.write(run/'output/execution.json',{'read_files':['input/source.md']})
            result=runner.finish(run,'synthetic-test',runner.now())
            self.assertEqual(result['status'],'task_failed')
            archive=root/'evidence'
            self.assertEqual(archiver.archive(runs,archive)['archived'],1)
            self.assertEqual((archive/'one/input/source.md').read_text(),'Wrongly modified by executor')
            self.assertEqual((archive/'one/output/answer.md').read_bytes(),(run/'output/answer.md').read_bytes())
            (run/'input/source.md').write_text('Post-run tampering')
            with self.assertRaisesRegex(ValueError,'after finalization'):
                archiver.archive(runs,archive)

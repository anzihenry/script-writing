import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_pipeline import ROOT


class ContextExperimentTest(unittest.TestCase):
    def test_formal_archive_is_complete_and_bound_to_frozen_preparation(self):
        with patch.object(sys, 'path', [str(ROOT / 'scripts')] + sys.path):
            spec = importlib.util.spec_from_file_location('context_experiment', ROOT / 'scripts/context_experiment.py')
            c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
            import grade_harness_runs as grader
        report = c.verify(c.EVAL / 'development')
        self.assertEqual(report['verified_runs'],24)
        self.assertTrue(report['matrix_complete'])
        self.assertTrue(all(row['input_unchanged'] and row['request_unchanged'] for row in report['rows']))
        self.assertEqual(c.costs(c.EVAL/'development'), grader.read(c.EVAL/'cost-observations.json'))
        for name,digest in grader.read(c.EVAL/'adjudication-input-hashes.json').items():
            self.assertEqual(grader.sha(c.EVAL/'adjudication'/name),digest)
        with tempfile.TemporaryDirectory() as tmp, patch.object(grader,'EVAL',c.EVAL):
            output=Path(tmp)/'grades.json'
            grader.summarize(c.EVAL/'development',c.EVAL/'blind-review',output,
                             c.EVAL/'adjudication/adjudication.json')
            self.assertEqual(grader.read(output),grader.read(c.EVAL/'final-grades.json'))

    def test_revision_boundary_preserves_bytes_outside_allowed_cell(self):
        with patch.object(sys, 'path', [str(ROOT / 'scripts')] + sys.path):
            spec = importlib.util.spec_from_file_location('context_experiment', ROOT / 'scripts/context_experiment.py')
            c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
        with tempfile.TemporaryDirectory() as tmp:
            source, revised = Path(tmp)/'source.md', Path(tmp)/'revised.md'
            before = '# Title\n| EP012-D002 | CHAR002 | 错误句。 |\n'
            source.write_bytes(before.encode())
            revised.write_bytes(before.replace('错误句。','候选句。').encode())
            self.assertTrue(c.revision_boundary(source,revised)['outside_edit_cell_unchanged'])
            revised.write_bytes(before.replace('Title','Changed title').encode())
            self.assertFalse(c.revision_boundary(source,revised)['outside_edit_cell_unchanged'])
            revised.write_bytes(before.replace('\n','\r\n').encode())
            self.assertFalse(c.revision_boundary(source,revised)['outside_edit_cell_unchanged'])

    def test_scenarios_have_expected_source_and_index_boundaries(self):
        with patch.object(sys, 'path', [str(ROOT / 'scripts')] + sys.path):
            spec = importlib.util.spec_from_file_location('context_experiment', ROOT / 'scripts/context_experiment.py')
            c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
        with tempfile.TemporaryDirectory() as tmp:
            p = c.module(c.PIPELINE)
            for task in c.TASKS:
                root = Path(tmp) / task['case_id']
                c.build_project(root, task)
                result = p.continuity_index(root, 'EP012')
                expected = 'UNVERIFIED' if task['case_id'] in {'N02','N03','N06'} else 'RECORDED'
                self.assertEqual(result['status'], expected)
                if expected == 'RECORDED':
                    self.assertEqual(result['states'][0]['value'], 'CHAR001商宁腰间')
                if task['case_id'] == 'N02':
                    self.assertIn('STALE', ' '.join(p.inspect(root, p.load(root))['bible']))
                if task['case_id'] == 'N03':
                    self.assertFalse((root / 'episodes/EP011-v1.0.md').exists())
                if task['case_id'] == 'N05':
                    self.assertTrue(any('RAIN-P1' in e for e in p.gate(root,p.load(root),'G5','EP012')[0]))

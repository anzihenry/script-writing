import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_pipeline import ROOT


class CandidateExperimentTest(unittest.TestCase):
    def test_development_changes_one_rule_and_preserves_common_inputs(self):
        with patch.object(sys,'path',[str(ROOT/'scripts')]+sys.path):
            spec=importlib.util.spec_from_file_location('candidate_experiment',ROOT/'scripts/candidate_experiment.py')
            c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);frozen=root/'frozen'
            c.freeze('dev',frozen)
            first,second=c.h.files(frozen/'baseline'),c.h.files(frozen/'candidate')
            self.assertEqual(first.keys(),second.keys())
            self.assertEqual([name for name in first if first[name]!=second[name]],[c.TARGET])
            self.assertEqual(c.matrix(frozen,root/'runs')['runs'],8)
            for task in ['S01','W01']:
                inputs=[]
                for condition in ['baseline','candidate']:
                    m=json.loads((root/'runs'/f'{task}-{condition}-r1/manifest.json').read_text())
                    inputs.append({n:h for n,h in m['input_hashes'].items() if not n.startswith('skills/')})
                self.assertEqual(*inputs)
            with self.assertRaisesRegex(ValueError,'exists'):c.matrix(frozen,root/'runs')
            (frozen/'candidate'/c.TARGET).write_text('Changed after freezing')
            with self.assertRaisesRegex(ValueError,'freeze changed'):c.matrix(frozen,root/'tampered')

    def test_holdout_uses_original_rubric_and_final_rules_without_development_tasks(self):
        with patch.object(sys,'path',[str(ROOT/'scripts')]+sys.path):
            spec=importlib.util.spec_from_file_location('candidate_holdout',ROOT/'scripts/candidate_experiment.py')
            c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);dev=base/'dev/frozen';holdout=base/'holdout/frozen'
            c.freeze('dev',dev)
            (base/'protocol.md').write_bytes((c.BASE/'protocol.md').read_bytes())
            with patch.object(c,'BASE',base):
                self.assertEqual(c.freeze('holdout',holdout,dev/'baseline')['tasks'],12)
            tasks=json.loads((holdout/'bank/tasks.json').read_text())['tasks']
            self.assertTrue(all(t['split']=='holdout' and t['case_id'] not in {'S01','W01'} for t in tasks))
            original=json.loads((c.M2/'rubric.json').read_text())['tasks']
            rubric=json.loads((holdout/'rubric.json').read_text())['tasks']
            self.assertEqual(rubric,{t['case_id']:original[t['case_id']] for t in tasks})
            self.assertEqual(c.h.files(holdout/'baseline'),c.h.files(holdout/'candidate'))
            self.assertEqual(c.matrix(holdout,base/'runs')['runs'],48)

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_pipeline import ROOT


class CandidateEvidenceTest(unittest.TestCase):
    def modules(self):
        with patch.object(sys, 'path', [str(ROOT/'scripts')]+sys.path):
            loaded=[]
            for name in ['candidate_experiment','measure_dependency_scope']:
                spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);loaded.append(module)
            import grade_harness_runs as grader
        return (*loaded,grader)

    def test_holdout_archive_has_all_frozen_runs_without_input_mutation(self):
        candidate,_,grader=self.modules();base=candidate.BASE/'holdout'
        report=candidate.verify(base)
        self.assertEqual(report['verified_runs'],48)
        self.assertTrue(report['matrix_complete'])
        self.assertTrue(all(r['input_unchanged'] and r['request_unchanged'] for r in report['rows']))
        history=grader.read(base/'execution-history.json')
        self.assertEqual(len(set(history['completed'])),48)
        self.assertIsNone(history['current_run'])
        self.assertEqual(history['archived_count'],48)

    def test_holdout_grades_preserve_independent_adjudication_and_recompute(self):
        candidate,_,grader=self.modules();base=candidate.BASE/'holdout'
        combined=grader.read(base/'adjudication/decisions.json')
        for category in ['routing','handoff']:
            folder=base/'adjudication'/category
            for name,digest in grader.read(folder/'input-hashes.json').items():
                self.assertEqual(grader.sha(folder/name),digest)
            self.assertEqual(combined['sources'][category],grader.sha(folder/'decisions.json'))
        with tempfile.TemporaryDirectory() as tmp,patch.object(grader,'EVAL',base):
            output=Path(tmp)/'grades.json'
            grader.summarize(base/'development',base/'blind-review',output,base/'adjudication/decisions.json')
            self.assertEqual(grader.read(output),grader.read(base/'final-grades.json'))

    def test_development_archive_and_adjudication_are_bound_and_recomputable(self):
        candidate,_,grader=self.modules();base=candidate.BASE/'dev'
        report=candidate.verify(base)
        self.assertEqual(report['verified_runs'],8)
        self.assertTrue(report['matrix_complete'])
        self.assertTrue(all(r['input_unchanged'] and r['request_unchanged'] for r in report['rows']))
        for name,digest in grader.read(base/'adjudication/input-hashes.json').items():
            self.assertEqual(grader.sha(base/'adjudication'/name),digest)
        with tempfile.TemporaryDirectory() as tmp,patch.object(grader,'EVAL',base):
            output=Path(tmp)/'grades.json'
            grader.summarize(base/'development',base/'blind-review',output,base/'adjudication/decisions.json')
            self.assertEqual(grader.read(output),grader.read(base/'final-grades.json'))
        decision=grader.read(base/'decision.json')
        self.assertEqual(decision['grade_sha256'],grader.sha(base/'initial-grades.json'))
        self.assertFalse(decision['candidate_merged'])

    def test_scope_assessments_and_pre_holdout_decisions_are_bound(self):
        candidate,scope,grader=self.modules();base=candidate.BASE
        self.assertEqual(scope.summarize(base/'scope'),grader.read(base/'scope/summary.json'))
        preflight=grader.read(base/'holdout/preflight.json')
        self.assertEqual(preflight['dev_decision_sha256'],grader.sha(base/'dev/decision.json'))
        self.assertEqual(preflight['scope_decision_sha256'],grader.sha(base/'scope/decision.json'))
        self.assertEqual(preflight['freeze_sha256'],grader.sha(base/'holdout/frozen/freeze.json'))
        # No candidate accepted: these labels do not encode a treatment difference.
        frozen=base/'holdout/frozen'
        self.assertEqual(candidate.h.files(frozen/'baseline'),candidate.h.files(frozen/'candidate'))
        expected=grader.read(frozen/'freeze.json')['files'];actual=candidate.h.files(frozen)
        actual.pop('freeze.json');self.assertEqual(actual,expected)
        with tempfile.TemporaryDirectory() as tmp:
            copied=Path(tmp)/'frozen';shutil.copytree(frozen,copied)
            self.assertEqual(candidate.matrix(copied,Path(tmp)/'runs')['runs'],48)
            self.assertEqual(grader.read(Path(tmp)/'prepared-runs.json'),
                             grader.read(base/'holdout/prepared-runs.json'))

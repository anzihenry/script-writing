import json
import shutil
import tempfile
import unittest
from pathlib import Path
from test_semantic_protocol import module
from test_pipeline import ROOT


class HarnessEvidenceTest(unittest.TestCase):
    def test_complete_development_archive_and_adjudicated_report_reproduce(self):
        verifier=module('verify_harness_evidence')
        grader=module('grade_harness_runs')
        base=ROOT/'docs/validation/v0.3.0/experiments'
        report=verifier.verify(base/'development')
        self.assertEqual(report['verified_runs'],72)
        self.assertTrue(report['matrix_complete'])
        for name,digest in grader.read(base/'adjudication-input-hashes.json').items():
            self.assertEqual(grader.sha(base/'adjudication'/name),digest)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'grades.json'
            grader.summarize(base/'development',base/'blind-review',output,
                             base/'adjudication/adjudication.json')
            self.assertEqual(grader.read(output),grader.read(base/'final-grades.json'))

    def test_frozen_preparation_rejects_self_consistent_manifest_tampering(self):
        verifier=module('verify_harness_evidence')
        original=ROOT/'docs/validation/v0.3.0/experiments/development/R01-A-r1'
        with tempfile.TemporaryDirectory() as tmp:
            runs=Path(tmp); run=runs/original.name
            shutil.copytree(original,run)
            report=verifier.verify(runs)
            self.assertEqual(report['verified_runs'],1)
            self.assertFalse(report['matrix_complete'])
            self.assertTrue(report['rows'][0]['input_matches_frozen'])
            source=run/'input/source.md'; source.write_text('Altered task source')
            manifest=verifier.read(run/'manifest.json')
            manifest['input_hashes']['source.md']=verifier.sha(source)
            (run/'manifest.json').write_text(json.dumps(manifest))
            result=verifier.read(run/'result.json')
            result['manifest_sha256']=verifier.sha(run/'manifest.json')
            result['actual_input_hashes']=manifest['input_hashes']
            (run/'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError,'differs from frozen preparation'):
                verifier.verify(runs)

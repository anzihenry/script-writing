import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_pipeline import ROOT, p


class DependencyScopeTest(unittest.TestCase):
    def test_six_changes_retain_originals_and_do_not_waive_stale_gates(self):
        with patch.object(sys,'path',[str(ROOT/'scripts')]+sys.path):
            spec=importlib.util.spec_from_file_location('scope_study',ROOT/'scripts/measure_dependency_scope.py')
            study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
        original=study.h.files(ROOT/'examples/return-season')
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'study';study.prepare(output)
            measurement=json.loads((output/'measurements.json').read_text())
            self.assertEqual(len(measurement['cases']),6)
            for case in measurement['cases']:
                folder=output/'reviews'/case['case_id']
                before,after=study.h.files(folder/'before'),study.h.files(folder/'after')
                self.assertEqual(before,original)
                self.assertTrue(all(after[name]==digest for name,digest in before.items() if name!='project.json'))
                self.assertEqual(case['impact']['source_change']['status'],'AVAILABLE')
                self.assertGreater(case['stale_artifacts'],0)
                data=p.load(folder/'after')
                self.assertTrue(p.inspect(folder/'after',data)['script_EP002'])
                self.assertTrue(p.gate(folder/'after',data,'G5','EP002')[0])
            self.assertEqual(study.h.files(ROOT/'examples/return-season'),original)

    def test_review_rejects_missing_artifacts_bad_quotes_and_changed_sources(self):
        with patch.object(sys,'path',[str(ROOT/'scripts')]+sys.path):
            spec=importlib.util.spec_from_file_location('scope_review',ROOT/'scripts/measure_dependency_scope.py')
            study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'study';study.prepare(output)
            case=output/'reviews/appearance';task=json.loads((case/'task.json').read_text())
            source='before/'+task['old_source'];quote=(case/source).read_text().splitlines()[0]
            # Synthetic schema fixture, not a semantic assessment of the example.
            rows=[{'artifact_id':key,'decision':'uncertain','locations':[],
                   'evidence':[{'path':source,'quote':quote}],'reason':'Synthetic validator fixture'}
                  for key in task['artifacts']]
            data={'case_id':'appearance','items':rows,'critical_locations':[],'limitations':[]}
            def save():study.h.write(case/'assessment.json',data)
            save();self.assertEqual(study.verify_review(case)['artifacts'],len(rows))
            data['items']=rows[:-1];save()
            with self.assertRaisesRegex(ValueError,'inventory'):study.verify_review(case)
            data['items']=rows;rows[0]['evidence'][0]['quote']='NONEXISTENT-QUOTE';save()
            with self.assertRaisesRegex(ValueError,'nonliteral'):study.verify_review(case)
            rows[0]['evidence'][0]['quote']=quote;rows[0]['evidence'][0]['path']='../measurements.json';save()
            with self.assertRaisesRegex(ValueError,'outside'):study.verify_review(case)
            rows[0]['evidence'][0]['path']=source;save()
            extra=case/'after/extra-source.md';extra.write_text('Unfrozen source')
            with self.assertRaisesRegex(ValueError,'input changed'):study.verify_review(case)
            extra.unlink()
            (case/source).write_text((case/source).read_text()+'\nchanged\n')
            with self.assertRaisesRegex(ValueError,'input changed'):study.verify_review(case)

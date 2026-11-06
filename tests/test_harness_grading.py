import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_semantic_protocol import module


class HarnessGradingTest(unittest.TestCase):
    def test_grades_require_original_quotes_complete_rubric_and_untampered_outputs(self):
        g=module('grade_harness_runs')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); evaluation=root/'evaluation'; (evaluation/'frozen').mkdir(parents=True)
            g.write(evaluation/'frozen/rubric.json',{'tasks':{'T':{'required':['Check']}}})
            g.write(evaluation/'frozen/freeze.json',{'files':{'rubric.json':g.sha(evaluation/'frozen/rubric.json')}})
            runs=root/'runs'; run=runs/'one'; run.mkdir(parents=True)
            blind=root/'blind'; output=blind/'category/outputs/anonymous'; output.mkdir(parents=True)
            (output/'answer.md').write_text('Actual answer with evidence.')
            result={'status':'completed','output_hashes':{'answer.md':g.sha(output/'answer.md')},'self_reported_unique_read_bytes':100,
                    'started_at':'2026-11-05T11:00:00Z','finished_at':'2026-11-05T16:00:00Z','timing_excluded_reason':'quota pause'}
            g.write(run/'result.json',result)
            g.write(runs/'blind-mapping.json',{'anonymous':{'run':str(run),'category':'category','task_id':'T','condition':'A','replicate':1,'result_sha256':g.sha(run/'result.json')}})
            (blind/'category/source.md').write_text('Synthetic source')
            g.write(runs/'blind-input-hashes.json',{'category/source.md':g.sha(blind/'category/source.md')})
            grade={'grades':[{'id':'anonymous','task_id':'T','required':[{'criterion':'Check','status':'pass','quote':'with evidence','reason':'Synthetic format-only grade'}],'critical_violations':[],'additional_findings':[]}]}
            path=blind/'category/grades.json'; g.write(path,grade)
            with patch.object(g,'EVAL',evaluation):
                self.assertEqual(g.summarize(runs,blind,root/'summary.json')['A']['successful'],1)
                self.assertIsNone(g.read(root/'summary.json')['rows'][0]['wall_seconds_upper_bound'])
                self.assertIsNone(g.median_known([None]))
                decision={**grade['grades'][0], 'category':'category',
                          'rationale':'Synthetic independent reassessment',
                          'task_rubric_alignment':'Synthetic test only'}
                decision['required']=[{'criterion':'Check','status':'fail','quote':'Actual answer','reason':'Synthetic failure'}]
                adjudication=root/'adjudication.json'; g.write(adjudication,{'decisions':[decision]})
                self.assertEqual(g.summarize(runs,blind,root/'reviewed.json',adjudication)['A']['successful'],0)
                row=g.read(root/'reviewed.json')['rows'][0]
                self.assertEqual(row['adjudication']['original_required'][0]['status'],'pass')
                self.assertEqual(g.read(path),grade)
                decision['task_id']='wrong'; g.write(adjudication,{'decisions':[decision]})
                with self.assertRaisesRegex(ValueError,'adjudication identity mismatch'):
                    g.summarize(runs,blind,root/'reviewed.json',adjudication)
                grade['grades'][0]['required'][0]['quote']='invented quote'; g.write(path,grade)
                with self.assertRaisesRegex(ValueError,'quote absent'): g.summarize(runs,blind,root/'summary.json')
                grade['grades'][0]['required']=[]; g.write(path,grade)
                with self.assertRaisesRegex(ValueError,'rubric mismatch'): g.summarize(runs,blind,root/'summary.json')
                grade['grades'][0]['required']=[{'criterion':'Check','status':'fail','quote':'','reason':'Synthetic missing evidence'}]; g.write(path,grade)
                (output/'answer.md').write_text('changed')
                with self.assertRaisesRegex(ValueError,'blinded output changed'): g.summarize(runs,blind,root/'summary.json')
                (blind/'category/source.md').write_text('Changed source')
                with self.assertRaisesRegex(ValueError,'blinded grading input changed'): g.summarize(runs,blind,root/'summary.json')

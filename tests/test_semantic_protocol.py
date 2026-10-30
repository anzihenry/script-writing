import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from test_pipeline import ROOT


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class SemanticProtocolTest(unittest.TestCase):
    def test_frozen_inputs_and_answer_coverage(self):
        folder = ROOT / 'docs/validation/v0.2.1/semantic'
        frozen = json.loads((folder / 'freeze.json').read_text())
        for name, digest in frozen['files'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)
        cases = json.loads((ROOT / 'tests/fixtures/semantic-long-range/cases.json').read_text())['cases']
        oracle = json.loads((folder / 'oracle.json').read_text())['cases']
        self.assertEqual(len(cases), 12)
        self.assertEqual({x['case_id'] for x in cases}, {x['case_id'] for x in oracle})
        self.assertEqual(sum(x['kind'] == 'positive' for x in oracle), 6)
        for case, answer in zip(cases, oracle):
            self.assertEqual(case['case_id'], answer['case_id'])
            self.assertEqual(case['fact_questions'], [x['question'] for x in answer['required_facts']])

    def test_round_packages_have_no_oracle_and_preserve_order(self):
        prep = module('prepare_semantic_round')
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / 'one', Path(tmp) / 'two'
            a, b = prep.prepare(first, 1), prep.prepare(second, 2)
            self.assertEqual(a['order'], list(reversed(b['order'])))
            self.assertFalse(any(x.name in {'oracle.json', 'freeze.json'} for x in first.rglob('*')))
            self.assertEqual({x.relative_to(first).as_posix() for x in first.rglob('*') if x.is_file()},
                             set(prep.RULES) | {'cases.json', 'manifest.json', 'request.md'})
            with self.assertRaises(ValueError):
                prep.prepare(first, 1)

    def test_output_validator_rejects_missing_cases_and_wrong_quotes(self):
        validate = module('validate_semantic_output').validate
        cases = json.loads((ROOT / 'tests/fixtures/semantic-long-range/cases.json').read_text())['cases']
        rows = []
        for case in cases:
            quote = case['source'].split('## EP001-SC001\n')[1].split('\n\n')[0]
            rows.append({'case_id': case['case_id'], 'findings': [], 'limitations': ['Synthetic format test, not an evaluation'],
                         'facts': [{'question': case['fact_questions'][0], 'answer': 'Synthetic format-only answer',
                                    'evidence': [{'location': 'EP001-SC001', 'quote': quote}]}]})
        self.assertEqual(validate({'cases': rows})['status'], 'STRUCTURE_OK')
        with self.assertRaises(ValueError):
            validate({'cases': rows[:-1]})
        rows[0]['facts'][0]['evidence'][0]['location'] = 'EP002-SC001'
        with self.assertRaises(ValueError):
            validate({'cases': rows})

    def test_archived_rounds_bind_grading_to_original_outputs(self):
        folder = ROOT / 'docs/validation/v0.2.1/semantic'
        oracle_hash = hashlib.sha256((folder / 'oracle.json').read_bytes()).hexdigest()
        public_hash = hashlib.sha256((ROOT / 'tests/fixtures/semantic-long-range/cases.json').read_bytes()).hexdigest()
        expected = {x['case_id']: x for x in json.loads((folder / 'oracle.json').read_text())['cases']}
        validate = module('validate_semantic_output').validate
        for number in [1, 2]:
            with self.subTest(round=number):
                run = folder / ('round-' + str(number))
                output_bytes = (run / 'outputs.json').read_bytes()
                outputs = json.loads(output_bytes)
                grade = json.loads((run / 'grading.json').read_text())
                manifest = json.loads((run / 'manifest.json').read_text())
                self.assertEqual(grade['outputs_sha256'], hashlib.sha256(output_bytes).hexdigest())
                self.assertEqual(grade['oracle_sha256'], oracle_hash)
                self.assertEqual(grade['cases_sha256'], public_hash)
                self.assertEqual([x['case_id'] for x in outputs['cases']], manifest['order'])
                self.assertEqual(validate(outputs), json.loads((run / 'structure-check.json').read_text()))
                self.assertEqual({x['case_id'] for x in grade['cases']}, set(expected))
                by_id = {x['case_id']: x for x in outputs['cases']}
                for row in grade['cases']:
                    out = by_id[row['case_id']]
                    for index in row['matched_finding_indices']:
                        self.assertIn(out['findings'][index]['severity'], ['P0', 'P1'])
                    for fact in row['facts']:
                        original = out['facts'][fact['output_fact_index']]
                        answer = expected[row['case_id']]['required_facts'][fact['oracle_fact_index']]
                        self.assertEqual(original['question'], answer['question'])
                        for index in fact['evidence_indices']:
                            self.assertTrue(original['evidence'][index]['quote'])
                summary = grade['summary']
                self.assertEqual(summary['preset_major_detected'], sum(len(x['matched_finding_indices']) for x in grade['cases']))
                self.assertEqual(summary['major_false_positives'], sum(len(x['major_false_positive_indices']) for x in grade['cases']))
                self.assertEqual(summary['complete_facts'], sum(f['assessment'] == 'complete' for x in grade['cases'] for f in x['facts']))
                self.assertEqual(summary['additional_findings'], sum(len(x['additional_finding_indices']) for x in grade['cases']))

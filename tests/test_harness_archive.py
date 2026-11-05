import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_pipeline import ROOT
from test_semantic_protocol import module


class HarnessArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.prep = module('prepare_semantic_round')
        for folder in ['docs/validation/v0.3.0/archive/v0.2.1', 'docs/validation/v0.2.1/semantic']:
            shutil.copytree(ROOT / folder, self.root / folder)
        self.public = self.root / self.prep.PUBLIC
        self.public.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / self.prep.PUBLIC, self.public)
        self.rule = self.root / self.prep.RULES[0]
        self.rule.parent.mkdir(parents=True)
        self.rule.write_text('# Changed current skill\n[example](example.md)\n')
        self.dependency = self.rule.parent / 'example.md'
        self.dependency.write_text('Current required example.\n')

    def test_current_changes_do_not_invalidate_history_but_archive_tampering_does(self):
        with patch.object(self.prep, 'ROOT', self.root):
            dest = Path(self.temp.name) / 'history'
            self.prep.prepare(dest, 1)
            self.assertNotEqual((dest / self.prep.RULES[0]).read_bytes(), self.rule.read_bytes())
            saved = self.root / self.prep.ARCHIVE / 'files' / self.prep.RULES[0]
            saved.write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'archived input changed'):
                self.prep.prepare(Path(self.temp.name) / 'bad', 1)
            self.assertFalse((Path(self.temp.name) / 'bad').exists())

    def test_current_package_records_actual_hashes_and_transitive_dependency(self):
        with patch.object(self.prep, 'ROOT', self.root), patch.object(self.prep.subprocess, 'check_output', side_effect=['commit\n', ' M skill\n']):
            dest = Path(self.temp.name) / 'current'
            result = self.prep.prepare(dest, 1, 'current', self.public, [self.prep.RULES[0]])
            self.assertTrue(result['source_dirty'])
            self.assertIn(self.dependency.relative_to(self.root).as_posix(), result['files'])
            for name, digest in result['files'].items():
                self.assertEqual(hashlib.sha256((dest / name).read_bytes()).hexdigest(), digest)
            self.assertFalse(any(x.name in {'oracle.json', 'outputs.json', 'freeze.json'} for x in dest.rglob('*')))
            with self.assertRaisesRegex(ValueError, 'refusing overwrite'):
                self.prep.prepare(dest, 1)

    def test_missing_or_escaping_dependencies_reject_without_partial_output(self):
        dest = Path(self.temp.name) / 'bad'
        with patch.object(self.prep, 'ROOT', self.root):
            self.dependency.unlink()
            with self.assertRaisesRegex(ValueError, 'missing rule dependency'):
                self.prep.prepare(dest, 1, 'current', self.public, [self.prep.RULES[0]])
            self.assertFalse(dest.exists())
            self.rule.write_text('[outside](../../../oracle.json)')
            with self.assertRaisesRegex(ValueError, 'outside skills'):
                self.prep.prepare(dest, 1, 'current', self.public, [self.prep.RULES[0]])

    def test_explicit_dataset_and_legacy_cli(self):
        outputs = ROOT / 'docs/validation/v0.2.1/semantic/round-1/outputs.json'
        data = json.loads(outputs.read_text())
        validate = module('validate_semantic_output').validate
        self.assertEqual(validate(data, self.public), validate(data))
        cases = json.loads(self.public.read_text())
        cases['cases'] = cases['cases'][:1]
        self.public.write_text(json.dumps(cases))
        self.assertEqual(validate({'cases': data['cases'][:1]}, self.public)['cases'], 1)
        with self.assertRaises(ValueError):
            validate(data, self.public)
        for extra in [[], ['--cases', str(ROOT / self.prep.PUBLIC)]]:
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_semantic_output.py'), str(outputs)] + extra, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_archive_cases_tamper_and_current_duplicate_ids(self):
        with patch.object(self.prep, 'ROOT', self.root):
            source = self.root / self.prep.ARCHIVE / 'files' / self.prep.PUBLIC
            source.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'archived input changed'):
                self.prep.archived_inputs()
            cases = json.loads(self.public.read_text())
            cases['cases'].append(cases['cases'][0])
            self.public.write_text(json.dumps(cases))
            with self.assertRaisesRegex(ValueError, 'duplicate case_id'):
                self.prep.prepare(Path(self.temp.name) / 'bad', 1, 'current', self.public, [self.prep.RULES[0]])

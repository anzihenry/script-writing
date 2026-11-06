import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_semantic_protocol import module
from test_pipeline import ROOT


class HarnessExperimentTest(unittest.TestCase):
    def test_authored_bank_is_reproducible(self):
        builder=module('build_harness_fixtures')
        with tempfile.TemporaryDirectory() as tmp:
            generated=Path(tmp)/'bank'
            with patch.object(builder,'ROOT',Path(tmp)), patch.object(builder,'DEST',generated), contextlib.redirect_stdout(io.StringIO()):
                builder.main()
            actual=ROOT/'tests/fixtures/harness-v0.3'
            for path in generated.rglob('*'):
                if path.is_file():
                    self.assertEqual(path.read_bytes(),(actual/path.relative_to(generated)).read_bytes(),str(path.relative_to(generated)))

    def test_bank_split_and_complete_scene_inputs(self):
        bank=ROOT/'tests/fixtures/harness-v0.3'
        tasks=json.loads((bank/'tasks.json').read_text())['tasks']
        self.assertEqual(len(tasks),24)
        for category in {t['category'] for t in tasks}:
            for split in ['dev','holdout']:
                self.assertEqual(sum(t['category']==category and t['split']==split for t in tasks),2)
        self.assertFalse({t['family'] for t in tasks if t['split']=='dev'} & {t['family'] for t in tasks if t['split']=='holdout'})
        for task in tasks:
            for file in task['files']: self.assertTrue((bank/'public'/task['case_id']/file).is_file())
            if task['long_form_episodes']:
                text=(bank/'public'/task['case_id']/'season.md').read_text()
                self.assertEqual(text.count('<!-- drama-table:v1 -->'),12)
                self.assertEqual(text.count('### 对白原文'),12)
                self.assertEqual(text.count('### 动作与时间预算'),12)

    def test_conditions_share_task_and_input_mutation_is_recorded(self):
        m=module('harness_experiment')
        with tempfile.TemporaryDirectory() as tmp:
            paths=[Path(tmp)/x for x in 'ABC']
            for c,path in zip('ABC',paths): m.prepare('R01',c,1,path,pilot=True)
            self.assertEqual((paths[0]/'input/request.md').read_bytes(),(paths[2]/'input/request.md').read_bytes())
            self.assertFalse((paths[0]/'input/skills').exists())
            self.assertTrue((paths[1]/'input/minimal.md').exists())
            self.assertTrue((paths[2]/'input/skills/ai-short-drama-writing/SKILL.md').exists())
            with self.assertRaises(ValueError): m.prepare('R03','A',1,Path(tmp)/'hold',pilot=True)
            (paths[0]/'input/source.md').write_text('modified')
            (paths[0]/'output/answer.md').write_text('Synthetic protocol-only answer')
            m.write(paths[0]/'output/execution.json',{'read_files':['input/source.md']})
            result=m.finish(paths[0],'synthetic-test',m.now())
            self.assertEqual(result['status'],'task_failed')
            self.assertIn('input mutation',result['errors'])
            with self.assertRaises(ValueError): m.finish(paths[0],'synthetic-test',m.now())

    def test_frozen_material_changes_rejected(self):
        m=module('harness_experiment')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); frozen=root/'frozen'; frozen.mkdir()
            (frozen/'input.txt').write_text('original')
            m.write(frozen/'freeze.json',{'files':m.files(frozen)})
            with patch.object(m,'EVAL',root):
                self.assertEqual(m.verify_freeze(),frozen)
                (frozen/'input.txt').write_text('changed')
                with self.assertRaises(ValueError): m.verify_freeze()

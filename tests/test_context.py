import copy
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from test_pipeline import p


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'project'
        self.output = self.base / 'packet'
        p.init_project(self.root, 'CONTEXT', 3)
        for kind in ['brief', 'bible', 'outline']:
            self.add(kind, 'project')
        for ep in ['EP001', 'EP002']:
            for kind in ['script', 'continuity', 'review', 'handoff']:
                self.add(kind, ep)

    def add(self, kind, scope):
        key = kind + '_' + scope
        name = key + '.md'
        (self.root / name).write_text('# Legacy fixture\nComplete source, no structured claims.\n')
        p.register(self.root, key, kind, scope, name, 'v1',
                   'reviewed' if kind in {'script', 'review'} else 'draft',
                   'Fixture-only evidence' if kind in {'script', 'review'} else None)
        return key

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob('*') if path.is_file()}

    def test_read_only_selection_current_target_prior_state_and_missing_target(self):
        before = self.snapshot()
        result = p.task_context(self.root, 'EP002', 'G3', self.output, 'Only revise EP002-D002')
        ids = {row['id'] for row in result['sources']}
        self.assertIn('script_EP002', ids)
        self.assertIn('script_EP001', ids)
        self.assertNotIn('handoff_EP002', ids)
        self.assertEqual(result['continuity']['through'], 'EP001')
        self.assertEqual(result['continuity']['status'], 'UNVERIFIED')
        self.assertEqual(result['authorization'], 'unspecified')
        self.assertEqual(p.verify_context(self.root, self.output)['status'], 'VERIFIED')
        self.assertEqual(self.snapshot(), before)
        missing = p.task_context(self.root, 'EP003', 'G3', self.base / 'missing')
        self.assertTrue(missing['blockers'])
        self.assertIn('script_EP002', {r['id'] for r in missing['sources']})
        self.assertEqual(self.snapshot(), before)

    def test_changed_source_copy_manifest_and_rule_are_detected(self):
        p.task_context(self.root, 'EP002', 'G3', self.output)
        source = self.root / 'script_EP001.md'
        original = source.read_bytes(); source.write_text('Changed after packet creation')
        self.assertEqual(p.verify_context(self.root, self.output)['status'], 'CHANGED')
        source.write_bytes(original)
        manifest = p.read_json(self.output / 'manifest.json')
        copied = self.output / manifest['sources'][0]['copy']
        original = copied.read_bytes(); copied.write_text('Corrupted copy')
        self.assertEqual(p.verify_context(self.root, self.output)['status'], 'CHANGED')
        copied.write_bytes(original)
        original_manifest = (self.output / 'manifest.json').read_bytes()
        modified = copy.deepcopy(manifest); modified['authorization'] = 'approved'
        p.write_json(self.output / 'manifest.json', modified)
        self.assertEqual(p.verify_context(self.root, self.output)['status'], 'CHANGED')
        (self.output / 'manifest.json').write_bytes(original_manifest)
        rule = self.output / manifest['rules'][0]['copy']
        rule.unlink()
        self.assertEqual(p.verify_context(self.root, self.output)['status'], 'CHANGED')

    def test_stale_checkpoint_issue_and_missing_material_remain_visible(self):
        p.checkpoint(self.root, 'CP', ['EP002'], 'Resume EP002', 'Read original sources')
        p.issue_action(self.root, 'add', 'I1', 'EP002', 'P1', 'EP002-SC001',
                       'Fixture issue', ['script_EP002'])
        (self.root / 'script_EP001.md').write_text('Unregistered change')
        (self.root / 'bible_project.md').unlink()
        before = self.snapshot()
        result = p.task_context(self.root, 'EP002', 'G3', self.output)
        self.assertTrue(any('STALE' in x for x in result['blockers']))
        self.assertIn('script_EP001', result['changed_since_checkpoint'])
        self.assertEqual(result['issues'][0]['status'], 'open')
        row = next(x for x in result['sources'] if x['id'] == 'bible_project')
        self.assertIsNone(row['copy'])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(p.verify_context(self.root, self.output)['status'], 'VERIFIED')

    def test_new_episode_inherits_latest_prior_checkpoint_but_not_future(self):
        p.checkpoint(self.root, 'PREVIOUS', ['EP001'], 'Continue EP002', 'EP001 ending')
        p.checkpoint(self.root, 'FUTURE', ['EP003'], 'Future work', 'EP003')
        before = self.snapshot()
        result = p.task_context(self.root, 'EP002', 'G3', self.output)
        self.assertEqual(result['checkpoint']['id'], 'PREVIOUS')
        self.assertEqual(self.snapshot(), before)

    def test_invalid_scope_overwrite_inside_project_and_escape_are_rejected(self):
        for scope, stage, output in [('EP999', 'G3', self.output), ('project', 'G3', self.output),
                                     ('EP001', 'G3', self.root / 'packet')]:
            with self.assertRaises(p.Invalid):
                p.task_context(self.root, scope, stage, output)
        p.task_context(self.root, 'EP002', 'G3', self.output)
        with self.assertRaises(p.Invalid):
            p.task_context(self.root, 'EP002', 'G3', self.output)
        manifest = p.read_json(self.output / 'manifest.json')
        manifest['sources'][0]['copy'] = '../escape.md'
        p.write_json(self.output / 'manifest.json', manifest)
        with self.assertRaises(p.Invalid):
            p.verify_context(self.root, self.output)

    def test_failed_creation_is_atomic_and_cli_exit_codes_match_contract(self):
        before = self.snapshot()
        with patch.object(p.shutil, 'copyfile', side_effect=OSError('fixture copy failure')):
            with self.assertRaises(OSError):
                p.task_context(self.root, 'EP002', 'G3', self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.snapshot(), before)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(p.main(['context', str(self.root), '--scope', 'EP002', '--stage', 'G3', '--output', str(self.output)]), 0)
            self.assertEqual(p.main(['verify-context', str(self.root), '--file', str(self.output)]), 0)
            self.assertEqual(p.main(['context', str(self.root), '--scope', 'EP003', '--stage', 'G3', '--output', str(self.base / 'missing')]), 1)
            self.assertEqual(p.main(['context', str(self.root), '--scope', 'project', '--stage', 'G3', '--output', str(self.base / 'bad')]), 2)
            (self.root / 'script_EP001.md').unlink()
            self.assertEqual(p.main(['verify-context', str(self.root), '--file', str(self.output)]), 1)

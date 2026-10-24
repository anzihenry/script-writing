import copy
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pipeline', ROOT / 'skills/ai-short-drama-writing/scripts/pipeline.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'show'
        p.init_project(self.root, 'TEST', 2)

    def add(self, kind, scope='project', status='draft', revision='v1.0', content=None):
        key = kind if scope == 'project' else f'{kind}_{scope}'
        path = f'{key}-{revision}.md'
        (self.root / path).write_text(content or f'# {key}\nActual test fixture content; not a creative-quality assertion.\n')
        p.register(self.root, key, kind, scope, path, revision, status,
                   'Test-only review evidence' if status in {'reviewed', 'locked'} else None)
        return key

    def chain(self, scope='EP001'):
        if not p.load(self.root)['artifacts']:
            for kind in ['brief', 'bible', 'outline']:
                self.add(kind)
        for kind in ['script', 'continuity', 'review', 'handoff']:
            self.add(kind, scope, 'reviewed' if kind in {'script', 'review'} else 'draft')

    def test_init_does_not_overwrite_and_does_not_pass_gate(self):
        with self.assertRaises(p.Invalid):
            p.init_project(self.root, 'OTHER', 1)
        self.assertTrue(p.gate(self.root, p.load(self.root), 'G0', 'project')[0])
        self.assertIn('{{episode_id}}', (p.HOME / 'assets/project-template/episode.md').read_text())
        self.assertNotIn('{{episode_id}}', (self.root / 'episodes/EP001-v1.0.md').read_text())

    def test_unfilled_template_and_missing_prerequisite_rejected(self):
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', 'brief.md', 'v1.0')
        with self.assertRaises(p.Invalid):
            self.add('script', 'EP001')

    def test_valid_chain_and_transitive_staleness(self):
        self.chain()
        self.assertFalse(p.gate(self.root, p.load(self.root), 'G5', 'EP001')[0])
        (self.root / 'bible-v1.0.md').write_text('Changed premise')
        result = p.inspect(self.root, p.load(self.root))
        self.assertTrue(result['bible'])
        self.assertTrue(result['handoff_EP001'])
        self.assertTrue(p.gate(self.root, p.load(self.root), 'G5', 'EP001')[0])

    def test_revision_and_dependency_refresh_require_evidence(self):
        self.chain()
        (self.root / 'brief-v1.0.md').write_text('New specification')
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', 'brief-v1.0.md', 'v1.0')
        p.register(self.root, 'brief', 'brief', 'project', 'brief-v1.0.md', 'v1.1')
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'bible', 'bible', 'project', 'bible-v1.0.md', 'v1.1')
        p.register(self.root, 'bible', 'bible', 'project', 'bible-v1.0.md', 'v1.1', note='Checked changed specification; story remains compatible.')
        self.assertTrue(p.inspect(self.root, p.load(self.root))['outline'])

    def test_next_episode_requires_previous_actual_continuity(self):
        for kind in ['brief', 'bible', 'outline']:
            self.add(kind)
        with self.assertRaises(p.Invalid):
            self.add('script', 'EP002')
        self.add('script', 'EP001')
        self.add('continuity', 'EP001')
        self.add('script', 'EP002')
        self.assertFalse(p.inspect(self.root, p.load(self.root))['script_EP002'])

    def test_cycles_and_missing_references_are_reported(self):
        self.chain()
        data = p.load(self.root)
        item = data['artifacts']['handoff_EP001']
        data['artifacts']['brief']['depends_on'] = [{'id': 'handoff_EP001', 'revision': item['revision'], 'sha256': item['sha256']}]
        self.assertTrue(p.inspect(self.root, data)['brief'])
        data['artifacts']['brief']['depends_on'][0]['id'] = 'missing'
        self.assertTrue(p.inspect(self.root, data)['brief'])

    def test_gate_scope_and_episode_isolation(self):
        self.chain()
        with self.assertRaises(p.Invalid):
            p.gate(self.root, p.load(self.root), 'G0', 'EP001')
        self.assertTrue(p.gate(self.root, p.load(self.root), 'G3', 'EP002')[0])
        self.assertFalse(p.gate(self.root, p.load(self.root), 'G5', 'EP001')[0])

    def test_issue_acceptance_and_revalidation(self):
        self.chain()
        data = p.load(self.root)
        issue = {'id': 'Q001', 'scope': 'EP001', 'severity': 'P1', 'status': 'open',
                 'location': 'EP001-SC001', 'summary': 'Timing needs correction', 'affects': ['script_EP001']}
        data['issues'].append(issue)
        p.validate_manifest(data)
        self.assertTrue(p.gate(self.root, data, 'G5', 'EP001')[0])
        issue.update(status='accepted', evidence='Named producer accepted this test exception', verified_revisions={'script_EP001': 'v1.0'})
        p.validate_manifest(data)
        self.assertFalse(p.gate(self.root, data, 'G5', 'EP001')[0])
        issue['severity'] = 'P0'
        with self.assertRaises(p.Invalid): p.validate_manifest(data)
        issue['severity'] = 'P1'
        data['artifacts']['script_EP001']['revision'] = 'v1.1'
        with self.assertRaises(p.Invalid): p.validate_manifest(data)

    def test_reviewed_requires_evidence_and_lock_preserves_original(self):
        (self.root / 'test.md').write_text('Test')
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', 'test.md', 'v1.0', 'reviewed')
        p.register(self.root, 'brief', 'brief', 'project', 'test.md', 'v1.0', 'locked', evidence='Explicit test approval')
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', 'test.md', 'v1.1')
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', './test.md', 'v1.1')
        (self.root / 'alias.md').symlink_to(self.root / 'test.md')
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', 'alias.md', 'v1.1')
        (self.root / 'new.md').write_text('New test')
        p.register(self.root, 'brief', 'brief', 'project', 'new.md', 'v1.1')
        self.assertEqual((self.root / 'test.md').read_text(), 'Test')
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', 'test.md', 'v1.2')

    def test_escape_and_symlink_escape_rejected(self):
        outside = self.root.parent / 'outside.md'
        outside.write_text('Outside')
        for path in ['../outside.md', str(outside)]:
            with self.assertRaises(p.Invalid):
                p.register(self.root, 'brief', 'brief', 'project', path, 'v1.0')
        (self.root / 'link.md').symlink_to(outside)
        with self.assertRaises(p.Invalid):
            p.register(self.root, 'brief', 'brief', 'project', 'link.md', 'v1.0')

    def test_archived_locked_baseline_tampering_is_detected(self):
        self.add('brief', status='locked')
        self.add('brief', revision='v1.1')
        (self.root / 'brief-v1.0.md').write_text('Tampered archived file')
        self.assertTrue(p.inspect(self.root, p.load(self.root))['brief'])

    def test_historical_revision_cannot_be_reused(self):
        self.add('brief')
        self.add('brief', revision='v1.1', content='New content')
        with self.assertRaises(p.Invalid):
            self.add('brief', revision='v1.0', content='Different content behind old version')

    def test_invalid_history_is_rejected(self):
        data = p.load(self.root)
        data['history'] = [None]
        with self.assertRaises(p.Invalid):
            p.validate_manifest(data)

    def test_bundle_includes_dependency_snapshots_and_refuses_overwrite(self):
        self.chain()
        output = self.root.parent / 'bundle.zip'
        self.assertEqual(p.bundle(self.root, 'EP001', output), 7)
        with zipfile.ZipFile(output) as archive:
            manifest = json.loads(archive.read('delivery-manifest.json'))
            for item in manifest['files'].values():
                self.assertEqual(p.hashlib.sha256(archive.read(item['path'])).hexdigest(), item['sha256'])
        with self.assertRaises(p.Invalid): p.bundle(self.root, 'EP001', output)

    def payload(self):
        return {'schema_version': '1.0', 'project_id': 'TEST', 'episode_id': 'EP001', 'revision': 'v1.0',
                'status': 'draft', 'source_script': 'script.md', 'bible_revision': 'v1.0', 'lock_evidence': None,
                'target_duration_seconds': {'min': 8, 'max': 10}, 'timing_basis': 'Unmeasured estimate',
                'assets': {'characters': [{'id': 'CHAR001', 'name': 'A'}],
                           'locations': [{'id': 'LOC001', 'name': 'Room'}], 'props': []},
                'scenes': [{'id': 'EP001-SC001', 'location_id': 'LOC001', 'time': 'Night',
                            'character_ids': ['CHAR001'], 'prop_ids': [], 'entry_state': 'Standing', 'exit_state': 'Seated',
                            'production_notes': [], 'blocks': [{'id': 'B001', 'duration_seconds': 8, 'action': 'Sits',
                            'dialogue': [{'id': 'D001', 'speaker_id': 'CHAR001', 'mode': 'on_screen', 'text': 'Hi'}],
                            'sound': [], 'screen_text': []}]}], 'unresolved': []}

    def test_handoff_invalid_types_references_duration_and_lock(self):
        self.assertEqual(p.validate_handoff(self.payload()), 8)
        for change in [lambda x: x['scenes'][0]['blocks'][0].update(duration_seconds=True),
                       lambda x: x['scenes'][0]['blocks'][0].update(duration_seconds=0),
                       lambda x: x['scenes'][0]['blocks'][0].update(duration_seconds=11),
                       lambda x: x['scenes'][0]['blocks'][0]['dialogue'][0].update(speaker_id='UNKNOWN'),
                       lambda x: x['scenes'][0]['blocks'][0]['dialogue'].append(copy.deepcopy(x['scenes'][0]['blocks'][0]['dialogue'][0])),
                       lambda x: x.update(status='locked')]:
            with self.subTest(change=change):
                data = self.payload(); change(data)
                with self.assertRaises(p.Invalid): p.validate_handoff(data)

    def test_bundle_rejects_export_from_different_version(self):
        self.chain()
        data = self.payload()
        data.update(status='reviewed', source_script='script_EP001-v1.0.md', revision='v9.0')
        (self.root / 'export.json').write_text(json.dumps(data))
        p.register(self.root, 'export_EP001', 'export', 'EP001', 'export.json', 'v1.0')
        with self.assertRaises(p.Invalid):
            p.bundle(self.root, 'EP001', self.root.parent / 'bad.zip')

    def test_duplicate_json_keys_rejected(self):
        path = self.root / 'bad.json'
        path.write_text('{"id":1,"id":2}')
        with self.assertRaises(p.Invalid): p.read_json(path)


if __name__ == '__main__':
    unittest.main()

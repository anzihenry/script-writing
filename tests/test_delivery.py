import json
import copy
import unittest
import test_management as management
from test_pipeline import p


class DeliveryTest(unittest.TestCase):
    setUp = management.ManagementTest.setUp
    add = management.ManagementTest.add
    chain = management.ManagementTest.chain

    def build(self):
        self.add('brief'); self.add('bible'); self.add('outline')
        self.source = {'scenes': [{'id': 'EP001-SC001', 'location_id': 'LOC001',
                       'character_ids': ['CHAR001', 'CHAR002'], 'prop_ids': ['PROP001'],
                       'dialogue': [{'id': 'EP001-D001', 'speaker_id': 'CHAR001', 'text': '谁？'}]}]}
        self.add('script', 'EP001', status='reviewed', content='```script-json\n' + json.dumps(self.source) + '\n```')
        self.add('continuity', 'EP001'); self.add('review', 'EP001', status='reviewed')
        self.target = dict(self.source, source_revision='v1.0')
        self.add('handoff', 'EP001', content='```handoff-json\n' + json.dumps(self.target) + '\n```')

    def test_parity_and_package_receipt(self):
        self.build()
        self.assertEqual(p.parity(self.root, 'EP001')['status'], 'MATCH')
        output = self.root.parent / 'one.zip'
        p.bundle(self.root, 'EP001', output, 'PK1')
        package = p.load(self.root)['deliveries'][0]
        self.assertEqual(package['status'], 'pending')
        self.assertEqual(package['sha256'], p.sha(output))
        p.receipt(self.root, 'PK1', 'returned', 'Simulated recipient found issue')
        p.feedback_action(self.root, 'add', 'F1', 'PK1', 'Simulated recipient', 'EP001-SC001', 'Test finding', 'production')
        with self.assertRaises(p.Invalid): p.feedback_action(self.root, 'update', 'F1', status='closed')
        p.feedback_action(self.root, 'update', 'F1', status='closed', verification='Simulated recheck evidence')
        result = p.measure(self.root, 'M1', 'PK1', 64, 'Synthetic test', 'Not a real recording')
        self.assertIsNone(result['delta_seconds'])
        with self.assertRaises(p.Invalid): p.measure(self.root, 'M2', 'PK1', float('nan'), 'x', 'x')
        with self.assertRaises(p.Invalid): p.bundle(self.root, 'EP001', self.root.parent / 'two.zip', 'PK1')

    def test_wrong_speaker_missing_line_and_old_version_block_bundle(self):
        self.build()
        for index, mode in enumerate(['speaker', 'missing', 'revision']):
            target = copy.deepcopy(self.target)
            if mode == 'speaker': target['scenes'][0]['dialogue'][0]['speaker_id'] = 'CHAR002'
            if mode == 'missing': target['scenes'][0]['dialogue'] = []
            if mode == 'revision': target['source_revision'] = 'v0.0'
            revision = f'v{index + 2}'
            self.add('handoff', 'EP001', revision=revision, content='```handoff-json\n' + json.dumps(target) + '\n```')
            self.assertEqual(p.parity(self.root, 'EP001')['status'], 'MISMATCH')
            with self.assertRaises(p.Invalid): p.bundle(self.root, 'EP001', self.root.parent / f'{index}.zip')

    def test_legacy_is_unverified_and_rollback_on_save_failure(self):
        self.chain()
        self.assertEqual(p.parity(self.root, 'EP001')['status'], 'UNVERIFIED')
        from unittest.mock import patch
        output = self.root.parent / 'failed.zip'
        with patch.object(p, 'save', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError): p.bundle(self.root, 'EP001', output)
        self.assertFalse(output.exists())

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

    def table(self, line='| EP001-D001 | CHAR001 | 谁？ |', revision='v1.0'):
        return ('<!-- drama-table:v1 -->\n正文来源版本：' + revision + '\n'
                '## 场次 EP001-SC001\n地点：LOC001\n人物：CHAR001, CHAR002\n道具：PROP001\n\n'
                '| 对白ID | 说话者 | 原文 |\n| --- | --- | --- |\n' + line + '\n')

    def test_readable_table_to_json_handoff(self):
        self.add('brief'); self.add('bible'); self.add('outline')
        self.add('script', 'EP001', status='reviewed', content=self.table())
        self.add('continuity', 'EP001'); self.add('review', 'EP001', status='reviewed')
        self.add('handoff', 'EP001', content=self.table())
        result = p.parity(self.root, 'EP001')
        self.assertEqual(result['status'], 'MATCH')
        self.assertEqual(result['formats']['script'], 'markdown-table-v1')
        target = p.markdown_scenes(self.table())
        self.add('handoff', 'EP001', revision='v2', content='```handoff-json\n' + json.dumps(target) + '\n```')
        self.assertEqual(p.parity(self.root, 'EP001')['status'], 'MATCH')

    def test_readable_differences_and_ambiguous_sources(self):
        self.build()
        for number, content in enumerate([self.table(''), self.table('| EP001-D001 | CHAR002 | 谁？ |'), self.table(revision='v0')]):
            self.add('handoff', 'EP001', revision=f't{number}', content=content)
            self.assertEqual(p.parity(self.root, 'EP001')['status'], 'MISMATCH')
        content = self.table() + '\n```handoff-json\n' + json.dumps(self.target) + '\n```'
        self.add('handoff', 'EP001', revision='ambiguous', content=content)
        with self.assertRaises(p.Invalid): p.parity(self.root, 'EP001')

    def test_readable_multiple_scenes_and_escaped_pipe(self):
        text = self.table('| EP001-D001 | CHAR001 | 左邊 \\| 右边 |')
        text += ('\n## 场次 EP001-SC002\n地点：LOC002\n人物：CHAR001\n道具：-\n\n'
                 '| 对白ID | 说话者 | 原文 |\n| --- | --- | --- |\n| EP001-D002 | CHAR001 | 走。 |\n')
        parsed = p.scene_projection(p.markdown_scenes(text), 'EP001')
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['dialogue'][0]['text'], '左邊 | 右边')
        self.assertEqual(parsed[1]['prop_ids'], [])
        with self.assertRaises(p.Invalid): p.markdown_scenes(self.table().replace('| --- | --- | --- |', '| -- | -- | -- |'))
        with self.assertRaises(p.Invalid): p.markdown_scenes(self.table().replace('| 对白ID | 说话者 | 原文 |', '| ID | 角色 | 文本 |'))

import copy
import json
import unittest
import test_pipeline as baseline
p = baseline.p


class EvidenceTest(unittest.TestCase):
    setUp = baseline.PipelineTest.setUp
    add = baseline.PipelineTest.add

    def source(self):
        return {'scenes': [
            {'id': 'EP001-SC001', 'location_id': 'LOC001', 'character_ids': ['CHAR001'], 'prop_ids': [],
             'dialogue': [{'id': 'EP001-D001', 'speaker_id': 'CHAR001', 'text': '左 | 右\n继续'}]},
            {'id': 'EP001-SC010', 'location_id': 'LOC001', 'character_ids': ['CHAR001'], 'prop_ids': [],
             'dialogue': [{'id': 'EP001-D010', 'speaker_id': 'CHAR001', 'text': '钥匙交给你。'}]}]}

    def run_index(self, source, location, quote, foreshadow=False):
        for kind in ['brief', 'bible']:
            self.add(kind)
        self.add('outline', content='```outline-json\n' + json.dumps({'foreshadows': [
            {'id': 'F1', 'plant': 'EP001', 'payoff': 'EP002'}]}) + '\n```')
        self.add('script', 'EP001', content=source)
        row = {'location': location, 'quote': quote}
        if foreshadow:
            row.update(id='F1', status='planted')
        else:
            row.update(object='PROP001', field='holder', before=None, after='CHAR001', temporal='current')
        payload = {'states': [] if foreshadow else [row], 'foreshadows': [row] if foreshadow else []}
        self.add('continuity', 'EP001', content='```continuity-json\n' + json.dumps(payload) + '\n```')
        return p.continuity_index(self.root, 'EP001')

    def json_text(self, source=None):
        return '```script-json\n' + json.dumps(source or self.source()) + '\n```'

    def test_json_decoding_and_exact_dialogue(self):
        self.assertEqual(self.run_index(self.json_text(), 'EP001-D001', '左 | 右\r\n继续')['status'], 'RECORDED')

    def test_wrong_location_and_prefix_collision(self):
        for location, quote in [('EP001-SC001', '钥匙交给你。'), ('EP001-D001', '钥匙交给你。'),
                                ('EP001-SC01', '左'), ('EP002-SC001', '左'), ('EP001-SC999', '左')]:
            for hint in [False, True]:
                with self.subTest(location=location, foreshadow=hint):
                    self.setUp()
                    with self.assertRaises(p.Invalid):
                        self.run_index(self.json_text(), location, quote, hint)

    def test_duplicate_definitions_rejected(self):
        source = self.source()
        source['scenes'].append(copy.deepcopy(source['scenes'][0]))
        with self.assertRaises(p.Invalid):
            self.run_index(self.json_text(source), 'EP001-SC001', '左')

    def test_legacy_prose_does_not_prove_state(self):
        result = self.run_index('EP001-SC001 钥匙交给你。', 'EP001-SC001', '钥匙交给你。')
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertEqual(result['states'], [])

    def test_commented_and_nested_examples_are_not_definitions(self):
        for text in ['<!--\n' + self.json_text() + '\n-->', '````markdown\n' + self.json_text() + '\n````']:
            with self.subTest(text=text):
                self.setUp()
                self.assertEqual(self.run_index(text, 'EP001-D001', '左')['status'], 'UNVERIFIED')

    def table(self):
        return ('<!-- drama-table:v1 -->\n## 场次 EP001-SC001\n地点：LOC001\n人物：CHAR001\n道具：-\n'
                '| 对白ID | 说话者 | 原文 |\n| --- | --- | --- |\n| EP001-D001 | CHAR001 | 左 \\| 右 |\n'
                '\n她把钥匙放在桌上。\n')

    def test_readable_action_and_escaped_dialogue(self):
        self.assertEqual(self.run_index(self.table(), 'EP001-D001', '左 | 右')['status'], 'RECORDED')
        self.setUp()
        self.assertEqual(self.run_index(self.table(), 'EP001-SC001', '钥匙放在桌上')['status'], 'RECORDED')

    def test_comments_fences_and_following_section_not_evidence(self):
        for suffix in ['<!-- 隐藏证据 -->', '```text\n隐藏证据\n```', '## 注释\n隐藏证据']:
            with self.subTest(suffix=suffix):
                self.setUp()
                with self.assertRaises(p.Invalid):
                    self.run_index(self.table() + suffix, 'EP001-SC001', '隐藏证据')

    def test_similar_dialogue_does_not_bind_other_action(self):
        source = self.source()
        source['scenes'][1]['dialogue'][0]['text'] = source['scenes'][0]['dialogue'][0]['text']
        text = self.json_text(source) + ('\n| 时间块 | 秒数 | 动作 |\n| --- | --- | --- |\n'
                                       '| EP001-SC010-B001 | 5 | 钥匙放在桌上 |\n')
        with self.assertRaises(p.Invalid):
            self.run_index(text, 'EP001-SC001', '钥匙放在桌上')

    def test_action_bound_to_json_scene(self):
        text = self.json_text() + ('\n| 时间块 | 秒数 | 动作 |\n| --- | --- | --- |\n'
                                  '| EP001-SC010-B001 | 5 | 钥匙放在桌上 |\n')
        self.assertEqual(self.run_index(text, 'EP001-SC010', '钥匙放在桌上')['status'], 'RECORDED')

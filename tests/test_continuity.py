import json
import test_management as management
import unittest
from test_pipeline import p


class ContinuityTest(unittest.TestCase):
    setUp = management.ManagementTest.setUp
    add = management.ManagementTest.add
    chain = management.ManagementTest.chain

    def build(self, before='room', temporal='current', pay=True):
        self.add('brief'); self.add('bible')
        self.add('outline', content='```outline-json\n' + json.dumps({'foreshadows': [{'id': 'F1', 'plant': 'EP001', 'payoff': 'EP002'}]}) + '\n```')
        for ep, old, new, time in [('EP001', None, 'room', 'current'), ('EP002', before, 'safe', temporal)]:
            self.add('script', ep, content=f'{ep}-SC001 Evidence moved')
            states = [{'object': 'PROP001', 'field': 'place', 'before': old, 'after': new,
                       'location': f'{ep}-SC001', 'quote': 'Evidence moved', 'temporal': time}]
            hints = [{'id': 'F1', 'status': 'planted' if ep == 'EP001' else 'paid', 'location': f'{ep}-SC001', 'quote': 'Evidence moved'}]
            self.add('continuity', ep, content='```continuity-json\n' + json.dumps({'states': states, 'foreshadows': hints if ep == 'EP001' or pay else []}) + '\n```')

    def test_index_history_and_no_premature_overdue(self):
        self.build()
        first = p.continuity_index(self.root, 'EP001')
        self.assertEqual(first['status'], 'RECORDED')
        self.assertFalse(first['foreshadows'][0]['due'])
        final = p.continuity_index(self.root)
        self.assertEqual(final['states'][0]['value'], 'safe')
        self.assertEqual(len(final['history']), 2)
        self.assertEqual(final['foreshadows'][0]['status'], 'paid')

    def test_conflict_and_overdue(self):
        self.build(before='outside', pay=False)
        result = p.continuity_index(self.root)
        self.assertEqual(result['states'][0]['status'], 'CONFLICT')
        self.assertEqual(result['foreshadows'][0]['assessment'], 'OVERDUE')

    def test_flashback_does_not_overwrite(self):
        self.build(before='outside', temporal='flashback')
        self.assertEqual(p.continuity_index(self.root)['states'][0]['value'], 'room')

    def test_stale_and_missing_are_unverified(self):
        self.build()
        (self.root / 'script_EP001-v1.0.md').write_text('edited')
        result = p.continuity_index(self.root)
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertEqual(result['states'], [])

    def test_quote_must_exist(self):
        self.build()
        path = self.root / 'continuity_EP002-v1.0.md'
        path.write_text(path.read_text().replace('Evidence moved', 'Invented evidence'))
        p.register(self.root, 'continuity_EP002', 'continuity', 'EP002', path.name, 'v1.1')
        with self.assertRaises(p.Invalid): p.continuity_index(self.root)

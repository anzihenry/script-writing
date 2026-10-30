"""Regression targets established against v0.2.0; fixtures never edit the examples."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_pipeline import p, ROOT


class ReliabilityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        shutil.copytree(ROOT / 'examples/return-season', self.root)

    @unittest.expectedFailure
    def test_incomplete_location_is_rejected(self):
        key = p.find(p.load(self.root), 'continuity', 'EP003')
        item = p.load(self.root)['artifacts'][key]
        path = self.root / item['path']
        path.write_text(path.read_text().replace('"location": "EP003-SC001"',
                                                '"location": "EP003-"', 1))
        p.register(self.root, key, 'continuity', 'EP003', item['path'], 'audit-v2')
        with self.assertRaises(p.Invalid):
            p.continuity_index(self.root)

    @unittest.expectedFailure
    def test_corrupted_package_cannot_be_accepted(self):
        package = self.root.parent / 'package.zip'
        p.bundle(self.root, 'EP001', package, 'AUDIT-PKG')
        package.write_bytes(b'corrupted')
        before = (self.root / 'project.json').read_bytes()
        with self.assertRaises(p.Invalid):
            p.receipt(self.root, 'AUDIT-PKG', 'accepted', 'Simulated receipt')
        self.assertEqual(before, (self.root / 'project.json').read_bytes())

    @unittest.expectedFailure
    def test_next_checks_each_file_once(self):
        with patch.object(p, 'inspect', wraps=p.inspect) as inspections, patch.object(p, 'sha', wraps=p.sha) as hashes:
            self.assertEqual(p.next_steps(self.root)['status'], 'STRUCTURE_READY')
        self.assertEqual(inspections.call_count, 1)
        self.assertEqual(hashes.call_count, 19)

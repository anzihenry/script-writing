import contextlib
import copy
import io
import unittest
from unittest.mock import patch
import test_reliability as baseline
from test_pipeline import p


class PackageIntegrityTest(unittest.TestCase):
    def setUp(self):
        baseline.ReliabilityTest.setUp(self)
        self.package = self.root.parent / 'package.zip'
        p.bundle(self.root, 'EP001', self.package, 'PKG1')

    def test_verify_is_read_only_and_moved_package_uses_identity(self):
        before = (self.root / 'project.json').read_bytes()
        self.assertEqual(p.verify_package(self.root, 'PKG1')['status'], 'VERIFIED')
        moved = self.package.with_name('moved.zip')
        self.package.rename(moved)
        self.assertEqual(p.verify_package(self.root, 'PKG1')['status'], 'UNVERIFIED')
        self.assertEqual(p.verify_package(self.root, 'PKG1', moved)['status'], 'VERIFIED')
        wrong = moved.with_name('wrong.zip'); wrong.write_bytes(b'wrong')
        self.assertEqual(p.verify_package(self.root, 'PKG1', wrong)['status'], 'MISMATCH')
        self.assertEqual(before, (self.root / 'project.json').read_bytes())
        receipt = p.receipt(self.root, 'PKG1', 'accepted', 'Simulated external receipt', moved)
        self.assertEqual(receipt['path'], str(self.package.resolve()))
        self.assertEqual(receipt['integrity']['status'], 'VERIFIED')

    def test_missing_package_receipt_does_not_claim_integrity(self):
        self.package.unlink()
        result = p.receipt(self.root, 'PKG1', 'accepted', 'Simulated external receipt')
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(result['integrity']['status'], 'UNVERIFIED')
        self.assertTrue(result['integrity']['reasons'])

    def test_corruption_after_previous_verification_is_not_cached(self):
        p.receipt(self.root, 'PKG1', 'accepted', 'Simulated receipt')
        self.package.write_bytes(b'damaged')
        self.assertEqual(p.verify_package(self.root, 'PKG1')['status'], 'MISMATCH')
        result = p.receipt(self.root, 'PKG1', 'returned', 'Simulated damaged package return')
        self.assertEqual(result['integrity']['status'], 'MISMATCH')
        self.assertEqual(p.load(self.root)['events'][-1]['before']['integrity']['status'], 'VERIFIED')
        self.assertEqual(p.receipt(self.root, 'PKG1', 'pending', 'Simulated pending')['status'], 'pending')

    def test_unreadable_and_unknown_package(self):
        with patch.object(p, 'sha', side_effect=PermissionError('simulated unreadable file')):
            self.assertEqual(p.verify_package(self.root, 'PKG1')['status'], 'UNVERIFIED')
        with self.assertRaises(p.Invalid):
            p.verify_package(self.root, 'UNKNOWN')

    def test_legacy_and_invalid_observations(self):
        data = p.load(self.root)
        self.assertNotIn('integrity', data['deliveries'][0])
        observation = p.verify_package(self.root, 'PKG1')
        for field, value in [('status', 'MISMATCH'), ('delivery_id', 'wrong'), ('expected_sha256', '0' * 64),
                             ('actual_sha256', 'invalid'), ('at', None), ('reasons', 'not a list')]:
            with self.subTest(field=field):
                invalid = copy.deepcopy(data)
                invalid['deliveries'][0]['integrity'] = dict(observation, **{field: value})
                with self.assertRaises(p.Invalid):
                    p.validate_manifest(invalid)

    def test_receipt_save_failure_preserves_manifest(self):
        before = (self.root / 'project.json').read_bytes()
        with patch.object(p, 'save', side_effect=OSError('simulated write failure')):
            with self.assertRaises(OSError):
                p.receipt(self.root, 'PKG1', 'accepted', 'Simulated receipt')
        self.assertEqual(before, (self.root / 'project.json').read_bytes())

    def test_cli_exit_codes(self):
        args = ['verify-package', str(self.root), '--id', 'PKG1']
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(p.main(args), 0)
            self.package.write_bytes(b'wrong')
            self.assertEqual(p.main(args), 1)
            self.package.unlink()
            self.assertEqual(p.main(args), 1)
            self.assertEqual(p.main(args[:-1] + ['UNKNOWN']), 2)

#!/usr/bin/env python3
"""Replay both examples in temporary copies, including simulated package receipts."""
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / 'skills/ai-short-drama-writing/scripts/pipeline.py'


def main():
    results = []
    for example, supported in [('return-demo', False), ('return-season', True)]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / example
            shutil.copytree(ROOT / 'examples' / example, root)
            commands = [(['check', str(root)], 0), (['next', str(root), '--json'], 0),
                        (['index', str(root)], 0 if supported else 1),
                        (['parity', str(root), '--scope', 'EP001'], 0 if supported else 1),
                        (['bundle', str(root), '--scope', 'EP001', '--output', str(Path(tmp) / 'package.zip'), '--delivery-id', 'SIM-PKG'], 0),
                        (['verify-package', str(root), '--id', 'SIM-PKG'], 0),
                        (['receipt', str(root), '--id', 'SIM-PKG', '--status', 'accepted', '--evidence', 'Simulated acceptance replay, not a real recipient'], 0)]
            for args, expected in commands:
                result = subprocess.run([sys.executable, str(PIPELINE)] + args, text=True, capture_output=True)
                if result.returncode != expected:
                    raise RuntimeError(f'{example}/{args[0]}: expected {expected}, got {result.returncode}: {result.stdout} {result.stderr}')
                row = {'example': example, 'command': args[0], 'exit_code': result.returncode}
                if args[0] in {'next', 'index', 'parity', 'verify-package', 'receipt'}:
                    payload = json.loads(result.stdout)
                    row['status'] = payload['status']
                    if args[0] == 'receipt':
                        row['integrity'] = payload['integrity']['status']
                results.append(row)
    print(json.dumps({'python': platform.python_version(), 'results': results}, indent=2))


if __name__ == '__main__':
    main()

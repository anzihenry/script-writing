#!/usr/bin/env python3
"""Measure command-local scans on synthetic chains; writes only temporary fixtures."""
import contextlib
import io
import json
import platform
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
import scale_fixture
from test_pipeline import p


def main():
    results = []
    for count in [3, 30, 100]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'project'
            data = scale_fixture.build(root, count)
            for command in ['next', 'status']:
                with contextlib.redirect_stdout(io.StringIO()), patch.object(p, 'inspect', wraps=p.inspect) as checks, patch.object(p, 'sha', wraps=p.sha) as hashes:
                    start = time.perf_counter()
                    code = p.main([command, str(root)])
                    seconds = time.perf_counter() - start
                results.append({'episodes': count, 'artifacts': len(data['artifacts']), 'command': command,
                                'exit_code': code, 'inspect_calls': checks.call_count,
                                'sha_calls': hashes.call_count, 'seconds': round(seconds, 6)})
    print(json.dumps({'python': platform.python_version(), 'platform': platform.platform(), 'results': results}, indent=2))


if __name__ == '__main__':
    main()

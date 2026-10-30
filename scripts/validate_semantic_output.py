#!/usr/bin/env python3
"""Validate output coverage and literal evidence only; semantic scoring stays separate."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(output):
    cases = json.loads((ROOT / 'tests/fixtures/semantic-long-range/cases.json').read_text(encoding='utf-8'))['cases']
    sources = {x['case_id']: x for x in cases}
    if not isinstance(output, dict) or not isinstance(output.get('cases'), list):
        raise ValueError('cases array required')
    seen, evidence_count = set(), 0
    for row in output['cases']:
        cid = row.get('case_id') if isinstance(row, dict) else None
        if cid not in sources or cid in seen:
            raise ValueError('unknown/duplicate case: ' + str(cid))
        seen.add(cid)
        source = sources[cid]
        parts = re.split(r'^## (EP\d{3,}-SC\d{3,})\s*\n', source['source'], flags=re.M)
        sections = dict(zip(parts[1::2], parts[2::2]))
        for field in ['findings', 'facts', 'limitations']:
            if not isinstance(row.get(field), list):
                raise ValueError(cid + ': ' + field + ' array required')
        if any(not isinstance(x, str) or not x.strip() for x in row['limitations']):
            raise ValueError(cid + ': invalid limitation')
        questions = []
        for finding in row['findings']:
            if not isinstance(finding, dict) or finding.get('severity') not in {'P0', 'P1', 'P2'}:
                raise ValueError(cid + ': invalid finding severity')
            if not all(isinstance(finding.get(k), str) and finding[k].strip() for k in ['summary', 'minimum_fix']):
                raise ValueError(cid + ': finding summary/minimum_fix required')
            if not isinstance(finding.get('affected_range'), list) or not finding['affected_range']:
                raise ValueError(cid + ': affected_range required')
        for fact in row['facts']:
            if not isinstance(fact, dict) or not isinstance(fact.get('answer'), str) or not fact['answer'].strip():
                raise ValueError(cid + ': fact answer required')
            questions.append(fact.get('question'))
        if questions != source['fact_questions']:
            raise ValueError(cid + ': fact questions missing, reordered or changed')
        for item in row['findings'] + row['facts']:
            if not isinstance(item.get('evidence'), list) or not item['evidence']:
                raise ValueError(cid + ': evidence required')
            for ref in item['evidence']:
                if not isinstance(ref, dict) or ref.get('location') not in sections:
                    raise ValueError(cid + ': unknown evidence location')
                quote = ref.get('quote')
                if not isinstance(quote, str) or not quote.strip() or quote not in sections[ref['location']]:
                    raise ValueError(cid + ': quote not found at ' + ref['location'])
                evidence_count += 1
    if seen != set(sources):
        raise ValueError('missing cases')
    return {'status': 'STRUCTURE_OK', 'cases': len(seen), 'evidence_references': evidence_count,
            'limitation': 'Literal evidence/coverage only; no semantic grading inferred.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(json.loads(args.output.read_text(encoding='utf-8'))), indent=2))
    except (ValueError, OSError, TypeError) as error:
        parser.exit(2, 'ERROR: ' + str(error) + '\n')

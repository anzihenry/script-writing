#!/usr/bin/env python3
"""Local, standard-library-only controls for the script production pipeline."""
import argparse
import copy
import hashlib
import json
import math
import re
import sys
import tempfile
import zipfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
KINDS = {'brief', 'bible', 'outline', 'script', 'continuity', 'review', 'handoff', 'export', 'season_review'}
STATES = {'draft', 'reviewed', 'locked', 'superseded'}
GATES = {'G0': ['brief'], 'G1': ['bible'], 'G2': ['outline'],
         'G3': ['script', 'continuity'], 'G4': ['review'], 'G5': ['handoff']}


class Invalid(ValueError):
    pass


def require(test, message):
    if not test:
        raise Invalid(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return type(value) in (float, int) and math.isfinite(value) and value > 0


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path):
    with Path(path).open(encoding='utf-8') as handle:
        return json.load(handle, object_pairs_hook=unique_object,
                         parse_constant=lambda value: (_ for _ in ()).throw(Invalid(f'nonfinite JSON: {value}')))


def write_json(path, value):
    path = Path(path)
    # Replace atomically; do not expose a partially written manifest.
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
        temporary = Path(handle.name)
    temporary.replace(path)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local(root, relative):
    require(nonempty(relative) and not Path(relative).is_absolute(), f'project-relative path required: {relative}')
    resolved = (root / relative).resolve()
    require(resolved.is_relative_to(root.resolve()), f'path escapes project: {relative}')
    return resolved


def validate_manifest(data):
    require(isinstance(data, dict) and data.get('schema_version') == '1.0', 'project schema_version must be 1.0')
    require(nonempty(data.get('project_id')), 'project_id required')
    require(isinstance(data.get('episodes'), list) and data['episodes'], 'nonempty episodes required')
    require(all(isinstance(e, str) and re.fullmatch(r'EP\d{3,}', e) for e in data['episodes']), 'invalid episode IDs')
    require(len(set(data['episodes'])) == len(data['episodes']), 'duplicate episode IDs')
    require(isinstance(data.get('artifacts'), dict), 'artifacts must be an object')
    require(isinstance(data.get('history'), list), 'history must be an array')
    require(isinstance(data.get('issues'), list), 'issues must be an array')
    for entry in data['history']:
        require(isinstance(entry, dict) and nonempty(entry.get('id')), 'invalid history entry')
        require(entry['id'] in data['artifacts'], 'history references unknown artifact')
        for field in ['previous', 'current']:
            snapshot = entry.get(field)
            require(snapshot is None or isinstance(snapshot, dict), 'invalid history snapshot')
            if snapshot is not None:
                require(all(nonempty(snapshot.get(f)) for f in ['path', 'revision', 'sha256']), 'incomplete history snapshot')
    occupied = set()
    paths = set()
    for key, item in data['artifacts'].items():
        require(re.fullmatch(r'[A-Za-z0-9_-]+', key) is not None, f'invalid artifact ID: {key}')
        require(isinstance(item, dict), f'{key}: artifact must be object')
        require(item.get('kind') in KINDS, f'{key}: invalid kind')
        require(item.get('scope') in ['project'] + data['episodes'], f'{key}: invalid scope')
        require((item['scope'] == 'project') == (item['kind'] in {'brief', 'bible', 'outline', 'season_review'}), f'{key}: kind/scope mismatch')
        pair = (item['kind'], item['scope'])
        require(pair not in occupied, f'duplicate active kind/scope: {pair}')
        occupied.add(pair)
        require(item.get('status') in STATES, f'{key}: invalid status')
        for field in ['path', 'revision', 'sha256']:
            require(nonempty(item.get(field)), f'{key}: {field} required')
        require(re.fullmatch(r'[0-9a-f]{64}', item['sha256']) is not None, f'{key}: invalid sha256')
        require(item['path'] not in paths, f'{key}: path already owned by another artifact')
        paths.add(item['path'])
        if item['status'] in {'reviewed', 'locked'}:
            require(nonempty(item.get('evidence')), f'{key}: review/lock evidence required')
        require(isinstance(item.get('depends_on'), list), f'{key}: depends_on must be array')
        seen = set()
        for dep in item['depends_on']:
            require(isinstance(dep, dict), f'{key}: dependency must be object')
            require(all(nonempty(dep.get(f)) for f in ['id', 'revision', 'sha256']), f'{key}: incomplete dependency snapshot')
            require(dep['id'] != key and dep['id'] not in seen, f'{key}: self or duplicate dependency')
            seen.add(dep['id'])
    issue_ids = set()
    for issue in data['issues']:
        require(isinstance(issue, dict), 'issue must be object')
        require(nonempty(issue.get('id')) and issue['id'] not in issue_ids, 'issue ID missing/duplicate')
        issue_ids.add(issue['id'])
        require(issue.get('scope') in ['project'] + data['episodes'], f"{issue['id']}: invalid scope")
        require(issue.get('severity') in {'P0', 'P1', 'P2'}, f"{issue['id']}: invalid severity")
        require(issue.get('status') in {'open', 'resolved', 'accepted'}, f"{issue['id']}: invalid issue status")
        require(nonempty(issue.get('location')) and nonempty(issue.get('summary')), f"{issue['id']}: location/summary required")
        require(isinstance(issue.get('affects'), list) and issue['affects'], f"{issue['id']}: affects required")
        require(all(isinstance(a, str) and a in data['artifacts'] for a in issue['affects']), f"{issue['id']}: unknown affected artifact")
        if issue['status'] != 'open':
            require(nonempty(issue.get('evidence')), f"{issue['id']}: resolution/acceptance evidence required")
            require(issue.get('verified_revisions') == {a: data['artifacts'][a]['revision'] for a in issue['affects']},
                    f"{issue['id']}: resolution/acceptance must be rechecked against current revisions")
        require(not (issue['severity'] == 'P0' and issue['status'] == 'accepted'), 'P0 cannot be waived')
    for field in ['events', 'checkpoints', 'feedback', 'deliveries', 'measurements']:
        require(isinstance(data.get(field, []), list), f'{field} must be an array')
        require(all(isinstance(x, dict) for x in data.get(field, [])), f'{field}: entries must be objects')
    validate_extensions(data)
    return data


def validate_extensions(data):
    def snapshot_map(value):
        require(isinstance(value, dict), 'snapshots must be an object')
        for key, item in value.items():
            require(key in data['artifacts'] and isinstance(item, dict), 'snapshot references unknown artifact')
            require(all(nonempty(item.get(f)) for f in ['path', 'revision', 'sha256']), 'incomplete snapshot')
            require(re.fullmatch(r'[0-9a-f]{64}', item['sha256']) is not None, 'invalid snapshot digest')
    for field in ['checkpoints', 'deliveries', 'feedback', 'measurements']:
        seen = set()
        for row in data.get(field, []):
            require(nonempty(row.get('id')) and row['id'] not in seen, f'{field}: missing/duplicate ID')
            seen.add(row['id'])
    for row in data.get('checkpoints', []):
        require(isinstance(row.get('scopes'), list) and row['scopes'] and all(e in data['episodes'] for e in row['scopes']), 'invalid checkpoint scopes')
        require(all(nonempty(row.get(f)) for f in ['at', 'next_entry', 'reread']), 'incomplete checkpoint')
        require(isinstance(row.get('open_issues'), list), 'invalid checkpoint issues')
        snapshot_map(row.get('snapshots'))
    packages = {x['id']: x for x in data.get('deliveries', [])}
    for row in packages.values():
        require(row.get('scope') in data['episodes'], 'invalid delivery scope')
        require(row.get('status') in {'pending', 'accepted', 'returned'}, 'invalid receipt status')
        require(all(nonempty(row.get(f)) for f in ['at', 'path', 'sha256']), 'incomplete delivery')
        require(re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is not None, 'invalid delivery digest')
        require(row.get('estimated_seconds') is None or number(row['estimated_seconds']), 'invalid estimate')
        require(isinstance(row.get('parity'), dict) and row['parity'].get('status') in {'MATCH', 'UNVERIFIED'}, 'invalid delivery parity')
        if row['status'] != 'pending':
            require(nonempty(row.get('evidence')), 'receipt evidence required')
        snapshot_map(row.get('files'))
        previous = row.get('supersedes')
        if previous:
            require(previous in packages and previous != row['id'] and packages[previous]['scope'] == row['scope'], 'invalid replacement package')
    issue_map = {x['id']: x for x in data['issues']}
    for row in data.get('feedback', []):
        require(all(nonempty(row.get(f)) for f in ['package_id', 'source', 'location', 'evidence']), 'incomplete feedback')
        require(row.get('layer') in {'script', 'production', 'unknown'}, 'invalid feedback layer')
        require(row.get('status') in {'triage', 'in_progress', 'awaiting_verification', 'closed'}, 'invalid feedback status')
        require(isinstance(row.get('issues'), list) and all(nonempty(x) and x in issue_map for x in row['issues']), 'unknown feedback issue')
        require(row['status'] == 'triage' or row['package_id'] in packages, 'unknown package must remain in triage')
        if row['status'] == 'closed':
            require(nonempty(row.get('verification')), 'feedback verification required')
            require(all(issue_map[x]['status'] != 'open' for x in row['issues']), 'closed feedback references open issue')
            require(row['layer'] != 'script' or row['issues'], 'closed script feedback needs issue')
    for row in data.get('measurements', []):
        require(row.get('package_id') in packages and number(row.get('seconds')), 'invalid measurement')
        require(all(nonempty(row.get(f)) for f in ['at', 'source', 'evidence']), 'measurement provenance required')
    for row in data.get('events', []):
        require(all(nonempty(row.get(f)) for f in ['at', 'type', 'id']), 'incomplete management event')
        require('before' in row and 'after' in row, 'event snapshots required')
        if row['type'] == 'impact':
            require(isinstance(row['after'], dict) and row['after'].get('source') in data['artifacts'], 'invalid impact event')
            snapshot_map(row['after'].get('snapshots'))


def load(root):
    return validate_manifest(read_json(Path(root) / 'project.json'))


def find(data, kind, scope):
    for key, item in data['artifacts'].items():
        if item['kind'] == kind and item['scope'] == scope:
            return key
    return None


def prerequisites(data, kind, scope):
    if kind == 'season_review':
        return [(k, ep) for ep in data['episodes'] for k in ['script', 'continuity']]
    needs = {'brief': [], 'bible': [('brief', 'project')],
             'outline': [('brief', 'project'), ('bible', 'project')],
             'script': [('bible', 'project'), ('outline', 'project')],
             'continuity': [('script', scope)],
             'review': [('script', scope), ('continuity', scope)],
             'handoff': [('script', scope), ('review', scope), ('bible', 'project'), ('continuity', scope)],
             'export': [('script', scope), ('handoff', scope)]}[kind]
    if kind == 'script':
        index = data['episodes'].index(scope)
        if index:
            needs.append(('continuity', data['episodes'][index - 1]))
    return needs


def inspect(root, data):
    """Return per-artifact errors, propagating stale dependencies transitively."""
    result, active = {}, set()

    def visit(key):
        if key in result:
            return result[key]
        if key in active:
            return [f'dependency cycle at {key}']
        active.add(key)
        item = data['artifacts'][key]
        errors = []
        try:
            path = local(root, item['path'])
            if not path.is_file():
                errors.append('file missing')
            elif sha(path) != item['sha256']:
                errors.append('file changed since registration (STALE)')
        except Invalid as error:
            errors.append(str(error))
        if item['status'] == 'superseded':
            errors.append('superseded artifact is not a usable current input')
        for entry in data['history']:
            previous = entry.get('previous') or {}
            if entry['id'] == key and previous.get('status') == 'locked':
                try:
                    baseline = local(root, previous['path'])
                    if not baseline.is_file() or sha(baseline) != previous['sha256']:
                        errors.append(f"archived locked baseline changed/missing: {previous['path']}")
                except Invalid as error:
                    errors.append(str(error))
        declared = {d['id'] for d in item['depends_on']}
        for kind, scope in prerequisites(data, item['kind'], item['scope']):
            dep_id = find(data, kind, scope)
            if dep_id is None or dep_id not in declared:
                errors.append(f'missing required dependency: {kind}/{scope}')
        for dep in item['depends_on']:
            current = data['artifacts'].get(dep['id'])
            if current is None:
                errors.append(f"dependency absent: {dep['id']}")
                continue
            if dep['revision'] != current['revision'] or dep['sha256'] != current['sha256']:
                errors.append(f"dependency snapshot outdated: {dep['id']}")
            if visit(dep['id']):
                errors.append(f"dependency unusable: {dep['id']}")
        active.remove(key)
        result[key] = errors
        return errors

    for key in data['artifacts']:
        visit(key)
    return result


def closure(data, keys):
    found = set()
    def walk(key):
        if key in found or key not in data['artifacts']:
            return
        found.add(key)
        for dep in data['artifacts'][key]['depends_on']:
            walk(dep['id'])
    for key in keys:
        walk(key)
    return found


def gate(root, data, stage, scope):
    require(stage in GATES, 'unknown gate')
    require((scope == 'project') == (stage in {'G0', 'G1', 'G2'}), 'gate/scope mismatch')
    require(scope in ['project'] + data['episodes'], 'unknown scope')
    errors, keys = [], []
    freshness = inspect(root, data)
    for kind in GATES[stage]:
        key = find(data, kind, scope)
        if key is None:
            errors.append(f'missing output: {kind}/{scope}')
        else:
            keys.append(key)
            errors.extend(f'{key}: {e}' for e in freshness[key])
    affected = closure(data, keys)
    for key in affected:
        item = data['artifacts'][key]
        if item['kind'] == 'review' and item['status'] not in {'reviewed', 'locked'}:
            errors.append(f'{key}: review conclusion not recorded as reviewed/locked')
        if stage == 'G5' and item['kind'] == 'script' and item['scope'] == scope and item['status'] not in {'reviewed', 'locked'}:
            errors.append(f'{key}: script not reviewed; draft preview is not a passed G5')
    for issue in data['issues']:
        relevant = (issue['scope'] in {'project', scope}) or bool(set(issue['affects']) & affected)
        if relevant and issue['status'] == 'open' and issue['severity'] in {'P0', 'P1'}:
            errors.append(f"{issue['id']}: unresolved {issue['severity']}: {issue['summary']}")
    return sorted(set(errors)), affected


def init_project(path, project_id, episodes):
    path = Path(path)
    require(not path.exists(), 'destination already exists; initialization never overwrites')
    require(nonempty(project_id) and episodes > 0 and episodes <= 999, 'project_id required; episodes must be 1..999')
    path.mkdir(parents=True)
    source = HOME / 'assets' / 'project-template'
    for name in ['brief', 'bible', 'outline', 'changes', 'decisions', 'feedback']:
        text = (source / f'{name}.md').read_text(encoding='utf-8')
        (path / f'{name}.md').write_text(text.replace('{{project_id}}', project_id), encoding='utf-8')
    episode_ids = [f'EP{i:03}' for i in range(1, episodes + 1)]
    for folder in ['episodes', 'continuity', 'reviews', 'handoff']:
        (path / folder).mkdir()
    for episode in episode_ids:
        for template, target in [('episode', f'episodes/{episode}-v1.0.md'),
                                 ('continuity', f'continuity/{episode}-v1.0.md'),
                                 ('review', f'reviews/{episode}-v1.0.md'),
                                 ('handoff', f'handoff/{episode}-v1.0.md')]:
            text = (source / f'{template}.md').read_text(encoding='utf-8')
            (path / target).write_text(text.replace('{{project_id}}', project_id).replace('{{episode_id}}', episode), encoding='utf-8')
    write_json(path / 'project.json', {'schema_version': '1.0', 'project_id': project_id,
                                     'episodes': episode_ids, 'artifacts': {}, 'issues': [], 'history': []})


def register(root, key, kind, scope, path, revision, status='draft', evidence=None, note=None):
    root = Path(root)
    data = load(root)
    require(kind in KINDS and status in STATES, 'invalid kind/status')
    require(scope in ['project'] + data['episodes'], 'unknown scope')
    require((scope == 'project') == (kind in {'brief', 'bible', 'outline', 'season_review'}), 'kind/scope mismatch')
    target = local(root, path)
    require(target.is_file(), f'file missing: {path}')
    # Canonical identity prevents ./ aliases or internal symlinks bypassing baseline preservation.
    path = target.relative_to(root.resolve()).as_posix()
    content = target.read_text(encoding='utf-8')
    require('<!-- TEMPLATE:UNFILLED -->' not in content, 'template not filled; remove sentinel only after writing actual content')
    if kind == 'season_review':
        assessment = review_check(root, path, revalidating=True)
        require(assessment['full_season'], 'registered season review must cover all project episodes')
        if status in {'reviewed', 'locked'}:
            require(assessment['status'] == 'PASS', 'season review has unverified/revision-needed dimensions')
    digest = sha(target)
    old = data['artifacts'].get(key)
    require(find(data, kind, scope) in {None, key}, 'another artifact owns this kind/scope; update its stable ID')
    for entry in data['history']:
        previous = entry.get('previous') or {}
        require(previous.get('status') != 'locked' or previous.get('path') != path,
                'cannot reuse an archived locked baseline path')
    if old:
        require((old['kind'], old['scope']) == (kind, scope), 'artifact identity cannot change kind/scope')
        if old['status'] == 'locked':
            require(local(root, old['path']).is_file() and sha(local(root, old['path'])) == old['sha256'], 'locked baseline changed or missing; restore it before registering a successor')
            require(path != old['path'], 'locked baseline needs a new path, even for metadata changes')
        if digest != old['sha256'] or old['status'] == 'locked':
            require(revision != old['revision'], 'changed content/locked successor needs a new revision')
    deps = []
    checks = inspect(root, data)
    for dep_kind, dep_scope in prerequisites(data, kind, scope):
        dep_id = find(data, dep_kind, dep_scope)
        require(dep_id is not None, f'missing prerequisite: {dep_kind}/{dep_scope}')
        require(not checks[dep_id], f'prerequisite needs repair/revalidation: {dep_id}')
        dep = data['artifacts'][dep_id]
        deps.append({'id': dep_id, 'revision': dep['revision'], 'sha256': dep['sha256']})
    if old and deps != old['depends_on']:
        require(nonempty(note), 'dependency refresh requires --note describing actual revalidation')
        require(revision != old['revision'], 'dependency refresh needs a new revision even if text is unchanged')
    item = {'kind': kind, 'scope': scope, 'path': path, 'revision': revision,
            'status': status, 'sha256': digest, 'depends_on': deps, 'evidence': evidence}
    for event in data['history']:
        previous = event.get('current') or {}
        if event['id'] == key and previous.get('revision') == revision:
            require(previous.get('sha256') == digest and previous.get('depends_on') == deps,
                    'cannot reuse a historical revision for different content/dependencies')
    data['artifacts'][key] = item
    data['history'].append({'at': stamp(), 'id': key, 'previous': old, 'current': copy.deepcopy(item), 'note': note})
    validate_manifest(data)
    write_json(root / 'project.json', data)


def event(data, kind, key, before, after, note=None):
    data.setdefault('events', []).append({'at': stamp(), 'type': kind, 'id': key,
        'before': copy.deepcopy(before), 'after': copy.deepcopy(after), 'note': note})


def save(root, data):
    validate_manifest(data)
    write_json(Path(root) / 'project.json', data)


def append_episodes(root, through):
    root = Path(root)
    data = load(root)
    require(type(through) is int and len(data['episodes']) <= through <= 999,
            'through must be current episode count..999; removal is unsupported')
    require(data['episodes'] == [f'EP{i:03}' for i in range(1, len(data['episodes']) + 1)],
            'append requires sequential EP001.. IDs; custom ordering is unsupported')
    added = [f'EP{i:03}' for i in range(len(data['episodes']) + 1, through + 1)]
    files = []
    for ep in added:
        for template, folder in [('episode', 'episodes'), ('continuity', 'continuity'),
                                 ('review', 'reviews'), ('handoff', 'handoff')]:
            target = local(root, f'{folder}/{ep}-v1.0.md')
            require(not target.exists() and not target.is_symlink(), f'target exists: {target}')
            require(target.parent.is_dir(), f'missing directory: {target.parent}')
            content = (HOME / 'assets' / 'project-template' / f'{template}.md').read_text(encoding='utf-8')
            files.append((target, content.replace('{{project_id}}', data['project_id']).replace('{{episode_id}}', ep)))
    if not added:
        return []
    before = list(data['episodes'])
    data['episodes'].extend(added)
    event(data, 'episodes', 'episodes', before, data['episodes'])
    validate_manifest(data)
    written = []
    try:
        for path, content in files:
            with path.open('x', encoding='utf-8') as handle:
                written.append(path)
                handle.write(content)
        save(root, data)
    except Exception:
        for path in written:
            path.unlink()
        raise
    return added


def issue_action(root, action, key=None, scope='project', severity='P1', location=None,
                 summary=None, affects=None, evidence=None, actor=None):
    data = load(root)
    if action == 'list':
        return data['issues']
    old = next((x for x in data['issues'] if x['id'] == key), None)
    before = copy.deepcopy(old)
    if action == 'add':
        require(old is None, 'issue already exists')
        item = {'id': key, 'scope': scope, 'severity': severity, 'status': 'open',
                'location': location, 'summary': summary, 'affects': affects or [],
                'evidence': None, 'verified_revisions': {}}
        data['issues'].append(item)
    else:
        require(old is not None, 'unknown issue')
        item = old
        if action == 'reopen':
            item.update(status='open', evidence=None, verified_revisions={})
            for feedback in data.get('feedback', []):
                if key in feedback['issues'] and feedback['status'] == 'closed':
                    previous = copy.deepcopy(feedback)
                    feedback.update(status='awaiting_verification', verification=None)
                    event(data, 'feedback', feedback['id'], previous, feedback, 'Linked issue reopened')
        else:
            require(action in {'resolve', 'accept'}, 'unknown issue action')
            require(nonempty(evidence), 'actual evidence required')
            checks = inspect(Path(root), data)
            require(all(not checks[a] for a in item['affects']), 'affected artifacts need revalidation')
            if action == 'accept':
                require(nonempty(actor), 'acceptance requires responsible actor')
                require(item['severity'] != 'P0', 'P0 cannot be waived')
            item.update(status='resolved' if action == 'resolve' else 'accepted', evidence=evidence,
                        verified_revisions={a: data['artifacts'][a]['revision'] for a in item['affects']})
            if actor:
                item['actor'] = actor
    event(data, 'issue', key, before, item, evidence)
    save(root, data)
    return item


def snapshots(data, keys=None):
    return {k: copy.deepcopy(v) for k, v in data['artifacts'].items() if keys is None or k in keys}


def checkpoint(root, key, scopes, next_entry, reread):
    data = load(root)
    require(nonempty(key) and nonempty(next_entry) and nonempty(reread), 'checkpoint id/next-entry/reread required')
    require(scopes and len(set(scopes)) == len(scopes) and all(e in data['episodes'] for e in scopes), 'invalid checkpoint scopes')
    require(not any(x.get('id') == key for x in data.get('checkpoints', [])), 'checkpoint ID already exists')
    keys = closure(data, [k for k, v in data['artifacts'].items() if v['scope'] in scopes or v['scope'] == 'project'])
    item = {'id': key, 'at': stamp(), 'scopes': scopes, 'snapshots': snapshots(data, keys),
            'open_issues': [x['id'] for x in data['issues'] if x['status'] == 'open'],
            'next_entry': next_entry, 'reread': reread}
    data.setdefault('checkpoints', []).append(item)
    save(root, data)
    return item


def next_steps(root, scope='project'):
    root = Path(root)
    data = load(root)
    require(scope == 'project' or scope in data['episodes'], 'unknown scope')
    episodes = data['episodes'] if scope == 'project' else data['episodes'][:data['episodes'].index(scope) + 1]
    stages = [('G0', 'project'), ('G1', 'project'), ('G2', 'project')]
    stages += [(g, ep) for ep in episodes for g in ['G3', 'G4', 'G5']]
    skills = dict(zip(GATES, ['brief', 'bible', 'outline', 'episode', 'review', 'handoff']))
    tasks = []
    for stage, target in stages:
        errors, _ = gate(root, data, stage, target)
        if errors:
            inputs = []
            for kind in GATES[stage]:
                for upstream_kind, upstream_scope in prerequisites(data, kind, target):
                    record = {'kind': upstream_kind, 'scope': upstream_scope,
                              'id': find(data, upstream_kind, upstream_scope)}
                    if record not in inputs:
                        inputs.append(record)
            tasks.append({'stage': stage, 'scope': target, 'reasons': errors,
                          'skill': 'ai-short-drama-' + skills[stage], 'inputs': inputs})
    checks = inspect(root, data)
    extras = {k: errors for k, errors in checks.items() if errors and data['artifacts'][k]['scope'] in ['project'] + episodes}
    if not tasks:
        for key, errors in extras.items():
            item = data['artifacts'][key]
            kind = item['kind']
            tasks.append({'stage': 'G4' if kind == 'season_review' else 'G5', 'scope': item['scope'],
                          'reasons': errors, 'skill': 'ai-short-drama-review' if kind == 'season_review' else 'ai-short-drama-handoff',
                          'inputs': [{'id': dep['id']} for dep in item['depends_on']]})
    latest = next((x for x in reversed(data.get('checkpoints', [])) if set(x['scopes']) & set(episodes)), None)
    changed = []
    if latest:
        changed = [k for k, v in latest['snapshots'].items()
                   if data['artifacts'].get(k) != v or checks.get(k)]
    return {'scope': scope, 'status': 'NEEDS_WORK' if tasks or extras else 'STRUCTURE_READY',
            'next': tasks[0] if tasks else None, 'tasks': tasks, 'artifact_errors': extras,
            'checkpoint': latest, 'changed_since_checkpoint': changed,
            'quality': 'Not inferred from structural readiness'}


def embedded(root, item, label):
    text = local(Path(root), item['path']).read_text(encoding='utf-8')
    matches = re.findall(r'^```' + re.escape(label) + r'\s*\n(.*?)^```\s*$', text, re.M | re.S)
    require(len(matches) <= 1, f'{label}: multiple blocks are ambiguous')
    if not matches:
        return None
    value = json.loads(matches[0], object_pairs_hook=unique_object,
                       parse_constant=lambda x: (_ for _ in ()).throw(Invalid('nonfinite JSON')))
    require(isinstance(value, dict), f'{label}: object required')
    return value


def continuity_index(root, through=None, object_id=None):
    root = Path(root)
    data = load(root)
    through = through or data['episodes'][-1]
    require(through in data['episodes'], 'unknown through episode')
    episodes = data['episodes'][:data['episodes'].index(through) + 1]
    checks = inspect(root, data)
    unknown, conflicts, history, values, hints = [], [], [], {}, {}
    outline = find(data, 'outline', 'project')
    plans = None
    if outline and not checks[outline]:
        plans = embedded(root, data['artifacts'][outline], 'outline-json')
    if plans is None:
        unknown.append('outline: missing/stale structured foreshadow plan')
        plans = {'foreshadows': []}
    require(isinstance(plans.get('foreshadows'), list), 'foreshadows must be an array')
    for plan in plans['foreshadows']:
        require(isinstance(plan, dict) and nonempty(plan.get('id')), 'invalid foreshadow plan')
        require(plan['id'] not in hints, 'duplicate foreshadow ID')
        require(plan.get('plant') in data['episodes'] and plan.get('payoff') in data['episodes'], 'unknown planned episode')
        require(data['episodes'].index(plan['plant']) <= data['episodes'].index(plan['payoff']), 'payoff before plant')
        hints[plan['id']] = dict(plan, status='not_planted', history=[])
    for ep in episodes:
        key, script = find(data, 'continuity', ep), find(data, 'script', ep)
        if key is None or script is None or checks.get(key) or checks.get(script):
            unknown.append(f'{ep}: continuity/script missing or stale')
            continue
        payload = embedded(root, data['artifacts'][key], 'continuity-json')
        if payload is None:
            unknown.append(f'{ep}: no continuity-json; extraction required')
            continue
        source = local(root, data['artifacts'][script]['path']).read_text(encoding='utf-8')
        require(isinstance(payload.get('states'), list) and isinstance(payload.get('foreshadows'), list), 'states/foreshadows arrays required')
        for row in payload['states'] + payload['foreshadows']:
            require(isinstance(row, dict) and nonempty(row.get('location')) and nonempty(row.get('quote')), 'location/quote required')
            require(row['location'].startswith(ep + '-') and row['location'] in source and row['quote'] in source,
                    f'{ep}: evidence not found in source')
        for row in payload['states']:
            require(all(nonempty(row.get(x)) for x in ['object', 'field', 'after']), 'object/field/after required')
            require('before' in row and (row['before'] is None or nonempty(row['before'])), 'before must be string or null')
            require(row.get('temporal') in {'current', 'flashback'}, 'temporal must be current/flashback')
            record = dict(row, episode=ep, script_revision=data['artifacts'][script]['revision'], script_sha256=data['artifacts'][script]['sha256'])
            history.append(record)
            identity = (row['object'], row['field'])
            if row['temporal'] == 'flashback':
                continue
            previous = values.get(identity)
            if previous and (previous['status'] == 'CONFLICT' or row['before'] != previous['value']):
                conflicts.append({'object': row['object'], 'field': row['field'], 'previous': previous, 'incoming': record})
                values[identity] = {'status': 'CONFLICT', 'value': None, 'evidence': record}
            else:
                values[identity] = {'status': 'RECORDED', 'value': row['after'], 'evidence': record}
        for row in payload['foreshadows']:
            require(row.get('id') in hints, 'actual foreshadow has no plan')
            require(row.get('status') in {'planted', 'paid', 'cancelled'}, 'invalid foreshadow status')
            hint = hints[row['id']]
            if row['status'] == 'cancelled':
                require(nonempty(row.get('reason')), 'cancellation reason required')
            if row['status'] == 'paid' and hint['status'] != 'planted':
                conflicts.append({'foreshadow': row['id'], 'reason': 'payoff without recorded planting', 'episode': ep})
            if hint['status'] in {'paid', 'cancelled'}:
                conflicts.append({'foreshadow': row['id'], 'reason': 'event after terminal state', 'episode': ep})
            hint['status'] = row['status']
            hint['history'].append(dict(row, episode=ep))
    for hint in hints.values():
        due = data['episodes'].index(hint['payoff']) <= data['episodes'].index(through)
        hint['due'] = due
        hint['assessment'] = 'UNVERIFIED' if unknown else ('OVERDUE' if due and hint['status'] not in {'paid', 'cancelled'} else 'RECORDED')
    overdue = any(x['assessment'] == 'OVERDUE' for x in hints.values())
    selected = [{'object': obj, 'field': field, **v} for (obj, field), v in values.items() if object_id is None or object_id == obj]
    if unknown:
        for value in selected:
            if value['status'] != 'CONFLICT':
                value['status'] = 'UNVERIFIED'
    if object_id and not selected:
        unknown.append(f'{object_id}: no current state recorded')
    return {'through': through, 'status': 'CONFLICT' if conflicts or overdue else ('UNVERIFIED' if unknown else 'RECORDED'),
            'coverage': episodes, 'unknown': unknown, 'conflicts': conflicts, 'states': selected,
            'history': [x for x in history if object_id is None or x['object'] == object_id],
            'foreshadows': list(hints.values()), 'limitation': 'Evidence existence checked; semantic extraction requires review'}


REVIEW_DIMENSIONS = {'character_arc', 'escalation', 'repetition', 'information', 'foreshadows', 'ending'}


def review_check(root, path, revalidating=False):
    data = load(root)
    payload = embedded(root, {'path': path}, 'review-json')
    require(payload is not None, 'review-json required')
    episodes = payload.get('episodes')
    require(isinstance(episodes, list) and episodes and all(nonempty(e) for e in episodes) and len(episodes) == len(set(episodes)), 'unique review episodes required')
    require(all(ep in data['episodes'] for ep in episodes), 'unknown reviewed episode')
    require(nonempty(payload.get('method')), 'actual review method required')
    dimensions = payload.get('dimensions')
    require(isinstance(dimensions, dict) and set(dimensions) == REVIEW_DIMENSIONS, 'all six season dimensions required')
    checks = inspect(Path(root), data)
    if not revalidating:
        for key, item in data['artifacts'].items():
            if item['kind'] == 'season_review' and local(Path(root), item['path']) == local(Path(root), path):
                require(not checks[key], 'registered season report is stale; perform and register revalidation')
    for ep in episodes:
        for kind in ['script', 'continuity']:
            key = find(data, kind, ep)
            require(key is not None and not checks[key], f'{ep}: review source missing/stale: {kind}')
    for name, result in dimensions.items():
        require(isinstance(result, dict) and result.get('status') in {'pass', 'revise', 'unverified'}, f'{name}: invalid conclusion')
        require(nonempty(result.get('evidence')), f'{name}: evidence/limitation required')
    affected = closure(data, [find(data, kind, ep) for ep in episodes for kind in ['script', 'continuity']])
    blockers = [x['id'] for x in data['issues'] if x['status'] == 'open' and x['severity'] in {'P0', 'P1'}
                and (x['scope'] in ['project'] + episodes or set(x['affects']) & affected)]
    status = 'PASS' if not blockers and all(x['status'] == 'pass' for x in dimensions.values()) else 'NEEDS_WORK'
    return {'status': status, 'full_season': episodes == data['episodes'], 'episodes': episodes,
            'method': payload['method'], 'dimensions': dimensions, 'blocking_issues': blockers,
            'limitation': 'Coverage declared by reviewer; semantic truth not machine-certified'}


def impact(root, key):
    data = load(root)
    require(key in data['artifacts'], 'unknown artifact')
    ordered, seen = [], set()
    def visit(current):
        if current in seen:
            return
        seen.add(current)
        for dep in data['artifacts'][current]['depends_on']:
            if dep['id'] in data['artifacts']:
                visit(dep['id'])
        ordered.append(current)
    for current in data['artifacts']:
        visit(current)
    checks = inspect(Path(root), data)
    affected = {key}
    rows = []
    for current in ordered:
        dependencies = {x['id'] for x in data['artifacts'][current]['depends_on']}
        if current != key and not dependencies & affected:
            continue
        affected.add(current)
        item = data['artifacts'][current]
        notes = [e['after'] for e in data.get('events', []) if e.get('type') == 'impact' and e.get('id') == current
                 and e['after'].get('source') == key and e['after'].get('snapshots') == snapshots(data, {key, current})]
        rows.append({'id': current, 'scope': item['scope'], 'kind': item['kind'],
                     'relation': 'source' if current == key else ('direct' if key in dependencies else 'transitive'),
                     'errors': checks[current], 'disposition': notes[-1] if notes else {'decision': 'pending'},
                     'content_diff': 'Use retained old/new files; registry snapshots are not content backups'})
    return {'source': key, 'order': rows, 'limitation': 'File-level dependency impact; semantic review still required'}


def impact_note(root, source, target, decision, evidence):
    report = impact(root, source)
    require(target in [x['id'] for x in report['order']], 'target is outside affected dependency closure')
    require(decision in {'rewrite', 'reviewed_unchanged', 'pending'} and nonempty(evidence), 'decision and evidence required')
    data = load(root)
    item = {'source': source, 'decision': decision, 'evidence': evidence, 'snapshots': snapshots(data, {source, target})}
    event(data, 'impact', target, None, item, evidence)
    save(root, data)
    return item


def feedback_action(root, action, key=None, package_id=None, source=None, location=None,
                    evidence=None, layer=None, issues=None, status=None, verification=None):
    data = load(root)
    if action == 'list':
        return data.get('feedback', [])
    old = next((x for x in data.get('feedback', []) if x['id'] == key), None)
    before = copy.deepcopy(old)
    require(nonempty(key), 'feedback ID required')
    if action == 'add':
        require(old is None, 'feedback ID already exists')
        item = {'id': key, 'package_id': package_id, 'source': source, 'location': location,
                'evidence': evidence, 'layer': layer, 'issues': issues or [], 'status': 'triage', 'verification': None}
        data.setdefault('feedback', []).append(item)
    else:
        require(action == 'update' and old is not None, 'unknown feedback')
        item = old
        for field, value in [('package_id', package_id), ('source', source), ('location', location),
                             ('evidence', evidence), ('layer', layer), ('issues', issues), ('status', status), ('verification', verification)]:
            if value is not None:
                item[field] = value
    require(all(nonempty(item.get(f)) for f in ['package_id', 'source', 'location', 'evidence', 'layer']), 'feedback source/package/location/evidence/layer required')
    require(item['layer'] in {'script', 'production', 'unknown'}, 'invalid feedback layer')
    require(item['status'] in {'triage', 'in_progress', 'awaiting_verification', 'closed'}, 'invalid feedback status')
    require(isinstance(item['issues'], list) and len(set(item['issues'])) == len(item['issues']), 'unique issue IDs required')
    known_issues = {x['id']: x for x in data['issues']}
    require(all(x in known_issues for x in item['issues']), 'unknown linked issue')
    known_package = any(x.get('id') == item['package_id'] for x in data.get('deliveries', []))
    require(known_package or item['status'] == 'triage', 'unknown package must remain in triage')
    if item['status'] == 'closed':
        require(nonempty(item.get('verification')), 'actual verification evidence required')
        require(all(known_issues[x]['status'] != 'open' for x in item['issues']), 'linked issues still open')
        if item['layer'] == 'script':
            require(item['issues'], 'script feedback requires linked issue before closing')
    event(data, 'feedback', key, before, item, verification or evidence)
    save(root, data)
    return item


def scene_projection(payload, scope, exported=False):
    require(isinstance(payload.get('scenes'), list) and payload['scenes'], 'nonempty scenes required')
    scenes, seen_scenes, seen_dialogue = [], set(), set()
    for scene in payload['scenes']:
        require(isinstance(scene, dict) and nonempty(scene.get('id')), 'scene ID required')
        require(scene['id'].startswith(scope + '-') and scene['id'] not in seen_scenes, 'duplicate/wrong-scope scene ID')
        seen_scenes.add(scene['id'])
        require(nonempty(scene.get('location_id')), 'location ID required')
        for field in ['character_ids', 'prop_ids']:
            value = scene.get(field)
            require(isinstance(value, list) and all(nonempty(x) for x in value) and len(value) == len(set(value)), f'invalid {field}')
        if exported:
            require(isinstance(scene.get('blocks'), list), 'blocks required')
            dialogue = [line for block in scene['blocks'] for line in block['dialogue']]
        else:
            dialogue = scene.get('dialogue')
        require(isinstance(dialogue, list), 'dialogue array required')
        lines = []
        for line in dialogue:
            require(isinstance(line, dict) and all(nonempty(line.get(x)) for x in ['id', 'speaker_id', 'text']), 'dialogue id/speaker/text required')
            require(line['id'].startswith(scope + '-') and line['id'] not in seen_dialogue, 'duplicate/wrong-scope dialogue ID')
            seen_dialogue.add(line['id'])
            require(line['speaker_id'] in scene['character_ids'], 'speaker absent from scene characters')
            lines.append({k: line[k].replace('\r\n', '\n') for k in ['id', 'speaker_id', 'text']})
        scenes.append({'id': scene['id'], 'location_id': scene['location_id'],
                       'character_ids': sorted(scene['character_ids']), 'prop_ids': sorted(scene['prop_ids']), 'dialogue': lines})
    return scenes


def markdown_cells(line):
    """Parse the supported three-column table; only escaped pipes are decoded."""
    require(line.startswith('|') and line.endswith('|'), 'dialogue table row must start/end with |')
    cells, current = [], []
    text = line[1:-1]
    i = 0
    while i < len(text):
        if text[i:i + 2] == '\\|':
            current.append('|')
            i += 2
        elif text[i] == '|':
            cells.append(''.join(current).strip())
            current = []
            i += 1
        else:
            current.append(text[i])
            i += 1
    cells.append(''.join(current).strip())
    require(len(cells) == 3, 'dialogue table needs exactly three columns')
    return cells


def markdown_scenes(text):
    marker = '<!-- drama-table:v1 -->'
    if marker not in text:
        return None
    require(text.count(marker) == 1, 'duplicate readable-format marker')
    result, current, table, separator, completed = {'scenes': []}, None, False, False, set()
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('正文来源版本：'):
            require('source_revision' not in result, 'duplicate source revision')
            result['source_revision'] = line.split('：', 1)[1].strip()
        match = re.fullmatch(r'## 场次 (EP\d{3,}-SC\d{3,})', line)
        if match:
            current = {'id': match.group(1), 'dialogue': []}
            result['scenes'].append(current)
            table = separator = False
            continue
        if current is None:
            if line.startswith('|'):
                require(not any(x in {'对白ID', '说话者', '原文'} or re.fullmatch(r'EP\d{3,}-D\d{3,}', x) for x in markdown_header(line)), 'dialogue table must belong to a scene')
            continue
        labels = {'地点：': 'location_id', '人物：': 'character_ids', '道具：': 'prop_ids'}
        found = False
        for prefix, field in labels.items():
            if line.startswith(prefix):
                require(field not in current, 'duplicate scene metadata: ' + field)
                value = line[len(prefix):].strip()
                current[field] = value if field == 'location_id' else ([] if value == '-' else [x.strip() for x in value.split(',')])
                found = True
                break
        if found:
            continue
        if line.startswith('|'):
            if not table:
                # Other action/timing tables are not dialogue; only this explicit header starts one.
                if markdown_header(line) != ['对白ID', '说话者', '原文']:
                    header = markdown_header(line)
                    require(not any(x in {'对白ID', '说话者', '原文'} or re.fullmatch(r'EP\d{3,}-D\d{3,}', x) for x in header), 'dialogue row/header outside supported table')
                    continue
                require(current['id'] not in completed, 'multiple dialogue tables in a scene')
                table = True
                separator = False
                continue
            cells = markdown_cells(line)
            if not separator:
                require(all(re.fullmatch(r':?-{3,}:?', x) for x in cells), 'Markdown separator required after dialogue header')
                separator = True
                completed.add(current['id'])
                continue
            require(not all(re.fullmatch(r':?-{3,}:?', x) for x in cells), 'unexpected table separator')
            current['dialogue'].append(dict(zip(['id', 'speaker_id', 'text'], cells)))
        elif table:
            require(separator, 'incomplete dialogue table')
            table = False
    require(result['scenes'] and all(x['id'] in completed for x in result['scenes']), 'every scene needs a complete dialogue table')
    return result


def markdown_header(line):
    # Ignore unrelated tables without imposing the dialogue table's column count.
    return [x.strip() for x in line.strip('|').split('|')]


def scene_document(root, item, label):
    structured = embedded(root, item, label)
    text = local(Path(root), item['path']).read_text(encoding='utf-8')
    readable = markdown_scenes(text)
    require(structured is None or readable is None, 'ambiguous dialogue source: choose JSON block or readable table, not both')
    return (readable, 'markdown-table-v1') if readable is not None else (structured, label if structured else 'unsupported')


def parity(root, scope):
    data = load(root)
    require(scope in data['episodes'], 'unknown episode')
    checks = inspect(Path(root), data)
    records = {kind: find(data, kind, scope) for kind in ['script', 'handoff', 'export']}
    missing = [kind for kind in ['script', 'handoff'] if records[kind] is None]
    stale = [kind for kind, key in records.items() if key and checks[key]]
    if missing or stale:
        return {'status': 'UNVERIFIED', 'reasons': ['missing: ' + ','.join(missing), 'stale: ' + ','.join(stale)]}
    script = data['artifacts'][records['script']]
    source, source_format = scene_document(root, script, 'script-json')
    target, target_format = scene_document(root, data['artifacts'][records['handoff']], 'handoff-json')
    if source is None or target is None:
        return {'status': 'UNVERIFIED', 'reasons': ['supported readable table/JSON block absent; legacy text requires manual review']}
    expected = scene_projection(source, scope)
    actual = scene_projection(target, scope)
    differences = []
    if target.get('source_revision') != script['revision']:
        differences.append('handoff source_revision differs from script')
    if expected != actual:
        differences.append('handoff scene/dialogue/speaker/asset coverage differs from script')
    if records['export']:
        export = read_json(local(Path(root), data['artifacts'][records['export']]['path']))
        validate_handoff(export)
        if export['project_id'] != data['project_id'] or export['episode_id'] != scope or export['revision'] != script['revision'] or export['source_script'] != script['path'] or export['status'] != script['status']:
            differences.append('export source identity/version/status differs from script')
        if scene_projection(export, scope, True) != expected:
            differences.append('export scene/dialogue/speaker/asset coverage differs from script')
    return {'status': 'MISMATCH' if differences else 'MATCH', 'reasons': differences,
            'formats': {'script': source_format, 'handoff': target_format},
            'coverage': ['scene order', 'scene locations', 'character/prop references', 'dialogue order/IDs', 'speaker', 'exact text'],
            'unverified': ['action semantics', 'performance', 'unstructured prose consistency'],
            'source': {'id': records['script'], 'revision': script['revision'], 'sha256': script['sha256']}}


def receipt(root, key, status, evidence):
    data = load(root)
    item = next((x for x in data.get('deliveries', []) if x['id'] == key), None)
    require(item is not None, 'unknown delivery')
    require(status in {'pending', 'accepted', 'returned'} and nonempty(evidence), 'status and actual receipt evidence required')
    before = copy.deepcopy(item)
    item.update(status=status, evidence=evidence)
    event(data, 'receipt', key, before, item, evidence)
    save(root, data)
    return item


def measure(root, key, package_id, seconds, source, evidence):
    data = load(root)
    require(nonempty(key) and not any(x['id'] == key for x in data.get('measurements', [])), 'unique measurement ID required')
    package = next((x for x in data.get('deliveries', []) if x['id'] == package_id), None)
    require(package is not None, 'unknown delivery')
    require(number(seconds) and nonempty(source) and nonempty(evidence), 'positive measured seconds/source/evidence required')
    estimate = package.get('estimated_seconds')
    item = {'id': key, 'package_id': package_id, 'seconds': seconds, 'source': source, 'evidence': evidence,
            'at': stamp(), 'estimated_seconds': estimate, 'delta_seconds': seconds - estimate if estimate is not None else None}
    data.setdefault('measurements', []).append(item)
    save(root, data)
    return item


def validate_handoff(data):
    """Explicit v1 contract, including cross references; not a generic JSON Schema engine."""
    require(isinstance(data, dict) and data.get('schema_version') == '1.0', 'handoff schema must be 1.0')
    for field in ['project_id', 'episode_id', 'revision', 'source_script', 'bible_revision', 'timing_basis']:
        require(nonempty(data.get(field)), f'{field} required')
    require(data.get('status') in STATES, 'invalid handoff status')
    require('lock_evidence' in data and (data['lock_evidence'] is None or nonempty(data['lock_evidence'])), 'invalid lock_evidence')
    if data['status'] == 'locked':
        require(nonempty(data['lock_evidence']), 'locked handoff requires evidence')
    target = data.get('target_duration_seconds')
    require(isinstance(target, dict) and number(target.get('min')) and number(target.get('max')) and target['min'] <= target['max'], 'invalid duration range')
    def strings(value, label):
        require(isinstance(value, list) and all(nonempty(v) for v in value), f'{label}: expected string array')
    strings(data.get('unresolved'), 'unresolved')
    assets = data.get('assets')
    require(isinstance(assets, dict), 'assets required')
    ids, by_kind = set(), {}
    def identifier(value, label):
        require(nonempty(value) and value not in ids, f'{label}: missing or duplicate ID {value}')
        ids.add(value)
    for kind in ['characters', 'locations', 'props']:
        require(isinstance(assets.get(kind), list), f'assets.{kind}: expected array')
        by_kind[kind] = set()
        for entry in assets[kind]:
            require(isinstance(entry, dict) and nonempty(entry.get('name')), f'{kind}: asset name required')
            identifier(entry.get('id'), kind)
            by_kind[kind].add(entry['id'])
    scenes = data.get('scenes')
    require(isinstance(scenes, list) and scenes, 'nonempty scenes required')
    total = 0
    for scene in scenes:
        require(isinstance(scene, dict), 'scene must be object')
        identifier(scene.get('id'), 'scene')
        require(scene.get('location_id') in by_kind['locations'], 'unknown location')
        for field in ['time', 'entry_state', 'exit_state']:
            require(nonempty(scene.get(field)), f'scene.{field} required')
        strings(scene.get('production_notes'), 'production_notes')
        for field, kind in [('character_ids', 'characters'), ('prop_ids', 'props')]:
            strings(scene.get(field), field)
            require(len(set(scene[field])) == len(scene[field]) and set(scene[field]) <= by_kind[kind], f'{field}: unknown/duplicate reference')
        require(isinstance(scene.get('blocks'), list) and scene['blocks'], 'nonempty blocks required')
        for block in scene['blocks']:
            require(isinstance(block, dict), 'block must be object')
            identifier(block.get('id'), 'block')
            require(number(block.get('duration_seconds')), 'duration must be positive finite number (not bool)')
            total += block['duration_seconds']
            require(nonempty(block.get('action')), 'action required')
            strings(block.get('sound'), 'sound')
            strings(block.get('screen_text'), 'screen_text')
            require(isinstance(block.get('dialogue'), list), 'dialogue array required')
            for line in block['dialogue']:
                require(isinstance(line, dict), 'dialogue must be object')
                identifier(line.get('id'), 'dialogue')
                require(line.get('speaker_id') in scene['character_ids'], 'speaker not registered in scene')
                require(line.get('mode') in {'on_screen', 'off_screen', 'inner', 'narration'}, 'invalid dialogue mode')
                require(nonempty(line.get('text')), 'dialogue text required')
    require(target['min'] <= total <= target['max'], f'duration {total} outside target')
    return total


def bundle(root, scope, output, delivery_id=None, supersedes=None):
    root, output = Path(root), Path(output)
    data = load(root)
    errors, selected = gate(root, data, 'G5', scope)
    require(not errors, '; '.join(errors))
    parity_result = parity(root, scope)
    require(parity_result['status'] != 'MISMATCH', 'handoff parity mismatch: ' + '; '.join(parity_result['reasons']))
    delivery_id = delivery_id or 'PKG-' + uuid.uuid4().hex[:16]
    require(nonempty(delivery_id) and not any(x['id'] == delivery_id for x in data.get('deliveries', [])), 'delivery ID already exists/invalid')
    if supersedes:
        require(any(x['id'] == supersedes and x['scope'] == scope for x in data.get('deliveries', [])), 'supersedes must name an existing delivery of this episode')
    estimated_seconds = None
    export = find(data, 'export', scope)
    if export:
        require(not inspect(root, data)[export], 'export is stale/invalid')
        selected |= closure(data, [export])
        payload = read_json(local(root, data['artifacts'][export]['path']))
        estimated_seconds = validate_handoff(payload)
        script = data['artifacts'][find(data, 'script', scope)]
        bible = data['artifacts'][find(data, 'bible', 'project')]
        require(payload['project_id'] == data['project_id'] and payload['episode_id'] == scope, 'export project/episode mismatch')
        require(payload['source_script'] == script['path'] and payload['revision'] == script['revision'] and payload['bible_revision'] == bible['revision'], 'export source/version mismatch')
        require(payload['status'] == script['status'], 'export/script status mismatch')
    require(not output.exists() and not output.is_symlink(), 'bundle destination exists; refusing overwrite')
    require(output.parent.is_dir(), 'bundle parent directory must exist')
    # Keep project dependencies in the package. No filesystem paths outside root are archived.
    manifest = {'schema_version': '1.0', 'delivery_id': delivery_id, 'supersedes': supersedes, 'parity': parity_result, 'project_id': data['project_id'], 'scope': scope,
                'created_at': stamp(), 'purpose': 'script-preproduction-handoff',
                'files': {key: data['artifacts'][key] for key in sorted(selected)},
                'issues': data['issues'], 'limitation': 'Structural checks only; no claim of creative approval or recipient acceptance.'}
    require(all(data['artifacts'][key]['path'] != 'delivery-manifest.json' for key in selected), 'artifact collides with package manifest')
    created = False
    try:
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            created = True
            archive.writestr('delivery-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
            for key in sorted(selected):
                item = data['artifacts'][key]
                archive.write(local(root, item['path']), item['path'])
        data.setdefault('deliveries', []).append({'id': delivery_id, 'scope': scope, 'at': stamp(),
            'files': snapshots(data, selected), 'sha256': sha(output), 'path': str(output.resolve()),
            'supersedes': supersedes, 'status': 'pending', 'evidence': None, 'parity': parity_result,
            'estimated_seconds': estimated_seconds})
        save(root, data)
    except Exception:
        if created:
            output.unlink()
        raise
    return len(selected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init'); p.add_argument('project'); p.add_argument('--id', required=True); p.add_argument('--episodes', type=int, default=1)
    p = sub.add_parser('register'); p.add_argument('project'); p.add_argument('--id', required=True); p.add_argument('--kind', choices=sorted(KINDS), required=True); p.add_argument('--scope', default='project'); p.add_argument('--path', required=True); p.add_argument('--revision', required=True); p.add_argument('--status', choices=sorted(STATES), default='draft'); p.add_argument('--evidence'); p.add_argument('--note')
    for cmd in ['check', 'status']:
        p = sub.add_parser(cmd); p.add_argument('project')
    p = sub.add_parser('gate'); p.add_argument('project'); p.add_argument('--stage', choices=list(GATES), required=True); p.add_argument('--scope', default='project')
    p = sub.add_parser('bundle'); p.add_argument('project'); p.add_argument('--scope', required=True); p.add_argument('--output', required=True); p.add_argument('--delivery-id'); p.add_argument('--supersedes')
    p = sub.add_parser('validate-handoff'); p.add_argument('file')
    p = sub.add_parser('episodes'); p.add_argument('project'); p.add_argument('--through', type=int, required=True)
    p = sub.add_parser('issue'); p.add_argument('project'); p.add_argument('action', choices=['add', 'list', 'resolve', 'reopen', 'accept'])
    p.add_argument('--id'); p.add_argument('--scope', default='project'); p.add_argument('--severity', choices=['P0', 'P1', 'P2'], default='P1')
    p.add_argument('--location'); p.add_argument('--summary'); p.add_argument('--affects', nargs='+'); p.add_argument('--evidence'); p.add_argument('--actor')
    p = sub.add_parser('next'); p.add_argument('project'); p.add_argument('--scope', default='project'); p.add_argument('--json', action='store_true')
    p = sub.add_parser('checkpoint'); p.add_argument('project'); p.add_argument('--id', required=True)
    p.add_argument('--scopes', nargs='+', required=True); p.add_argument('--next-entry', required=True); p.add_argument('--reread', required=True)
    p = sub.add_parser('index'); p.add_argument('project'); p.add_argument('--through'); p.add_argument('--object')
    p = sub.add_parser('review-check'); p.add_argument('project'); p.add_argument('--file', required=True)
    p = sub.add_parser('impact'); p.add_argument('project'); p.add_argument('--id', required=True)
    p = sub.add_parser('impact-note'); p.add_argument('project'); p.add_argument('--source', required=True); p.add_argument('--target', required=True)
    p.add_argument('--decision', choices=['rewrite', 'reviewed_unchanged', 'pending'], required=True); p.add_argument('--evidence', required=True)
    p = sub.add_parser('feedback'); p.add_argument('project'); p.add_argument('action', choices=['add', 'update', 'list'])
    for flag in ['id', 'package-id', 'source', 'location', 'evidence', 'layer', 'status', 'verification']:
        p.add_argument('--' + flag)
    p.add_argument('--issues', nargs='*')
    p = sub.add_parser('parity'); p.add_argument('project'); p.add_argument('--scope', required=True)
    p = sub.add_parser('receipt'); p.add_argument('project'); p.add_argument('--id', required=True)
    p.add_argument('--status', choices=['pending', 'accepted', 'returned'], required=True); p.add_argument('--evidence', required=True)
    p = sub.add_parser('measure'); p.add_argument('project'); p.add_argument('--id', required=True); p.add_argument('--package-id', required=True)
    p.add_argument('--seconds', type=float, required=True); p.add_argument('--source', required=True); p.add_argument('--evidence', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'parity':
            result = parity(args.project, args.scope)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['status'] == 'MATCH' else 1
        elif args.command == 'receipt':
            print(json.dumps(receipt(args.project, args.id, args.status, args.evidence), ensure_ascii=False, indent=2))
        elif args.command == 'measure':
            print(json.dumps(measure(args.project, args.id, args.package_id, args.seconds, args.source, args.evidence), ensure_ascii=False, indent=2))
        elif args.command == 'impact':
            print(json.dumps(impact(args.project, args.id), ensure_ascii=False, indent=2))
        elif args.command == 'impact-note':
            print(json.dumps(impact_note(args.project, args.source, args.target, args.decision, args.evidence), ensure_ascii=False, indent=2))
        elif args.command == 'feedback':
            print(json.dumps(feedback_action(args.project, args.action, args.id, args.package_id, args.source,
                args.location, args.evidence, args.layer, args.issues, args.status, args.verification), ensure_ascii=False, indent=2))
        elif args.command == 'review-check':
            result = review_check(args.project, args.file)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['status'] == 'PASS' else 1
        elif args.command == 'index':
            result = continuity_index(args.project, args.through, args.object)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['status'] == 'RECORDED' else 1
        elif args.command == 'next':
            result = next_steps(args.project, args.scope)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(result['status'])
                for task in result['tasks']:
                    print(f"{task['stage']}/{task['scope']} -> {task['skill']}: " + '; '.join(task['reasons']))
                if result['artifact_errors']:
                    print('Artifact checks: ' + json.dumps(result['artifact_errors'], ensure_ascii=False))
                if result['checkpoint']:
                    print('Checkpoint: ' + result['checkpoint']['id'] + '; changed: ' + ', '.join(result['changed_since_checkpoint']))
                    print('Resume: ' + result['checkpoint']['next_entry'] + '; reread: ' + result['checkpoint']['reread'])
        elif args.command == 'checkpoint':
            print(json.dumps(checkpoint(args.project, args.id, args.scopes, args.next_entry, args.reread), ensure_ascii=False, indent=2))
        elif args.command == 'episodes':
            print(json.dumps({'added': append_episodes(args.project, args.through)}, ensure_ascii=False))
        elif args.command == 'issue':
            print(json.dumps(issue_action(args.project, args.action, args.id, args.scope, args.severity,
                args.location, args.summary, args.affects, args.evidence, args.actor), ensure_ascii=False, indent=2))
        elif args.command == 'init':
            init_project(args.project, args.id, args.episodes)
            print('INITIALIZED: blank templates only; no stage passed')
        elif args.command == 'register':
            register(args.project, args.id, args.kind, args.scope, args.path, args.revision, args.status, args.evidence, args.note)
            print('REGISTERED: metadata recorded; creative quality not inferred')
        elif args.command == 'validate-handoff':
            print(f'STRUCTURE_OK: {validate_handoff(read_json(args.file))} seconds; text parity requires review')
        elif args.command == 'bundle':
            print(f'BUNDLED: {bundle(args.project, args.scope, args.output, args.delivery_id, args.supersedes)} artifacts; not sent to recipient')
        else:
            root = Path(args.project)
            data = load(root)
            if args.command == 'check':
                problems = inspect(root, data)
                failures = [f'{key}: {error}' for key, errors in problems.items() for error in errors]
                print('\n'.join(failures) if failures else 'STRUCTURE_OK: registered artifacts consistent; use gate for completeness')
                return 1 if failures else 0
            if args.command == 'gate':
                errors, _ = gate(root, data, args.stage, args.scope)
                print('\n'.join(errors) if errors else 'STRUCTURE_READY: perform/document the human quality gate; no status auto-promotion')
                return 1 if errors else 0
            for stage in GATES:
                scopes = ['project'] if stage in {'G0', 'G1', 'G2'} else data['episodes']
                for scope in scopes:
                    errors, _ = gate(root, data, stage, scope)
                    print(f'{stage}/{scope}: ' + ('NEEDS_WORK: ' + '; '.join(errors) if errors else 'STRUCTURE_READY'))
        return 0
    except (Invalid, OSError, json.JSONDecodeError, UnicodeError, TypeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())

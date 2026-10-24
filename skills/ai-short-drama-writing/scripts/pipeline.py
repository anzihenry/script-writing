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
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
KINDS = {'brief', 'bible', 'outline', 'script', 'continuity', 'review', 'handoff', 'export'}
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
        require((item['scope'] == 'project') == (item['kind'] in {'brief', 'bible', 'outline'}), f'{key}: kind/scope mismatch')
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
    return data


def load(root):
    return validate_manifest(read_json(Path(root) / 'project.json'))


def find(data, kind, scope):
    for key, item in data['artifacts'].items():
        if item['kind'] == kind and item['scope'] == scope:
            return key
    return None


def prerequisites(data, kind, scope):
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
    require((scope == 'project') == (kind in {'brief', 'bible', 'outline'}), 'kind/scope mismatch')
    target = local(root, path)
    require(target.is_file(), f'file missing: {path}')
    # Canonical identity prevents ./ aliases or internal symlinks bypassing baseline preservation.
    path = target.relative_to(root.resolve()).as_posix()
    content = target.read_text(encoding='utf-8')
    require('<!-- TEMPLATE:UNFILLED -->' not in content, 'template not filled; remove sentinel only after writing actual content')
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


def bundle(root, scope, output):
    root, output = Path(root), Path(output)
    data = load(root)
    errors, selected = gate(root, data, 'G5', scope)
    require(not errors, '; '.join(errors))
    export = find(data, 'export', scope)
    if export:
        require(not inspect(root, data)[export], 'export is stale/invalid')
        selected |= closure(data, [export])
        payload = read_json(local(root, data['artifacts'][export]['path']))
        validate_handoff(payload)
        script = data['artifacts'][find(data, 'script', scope)]
        bible = data['artifacts'][find(data, 'bible', 'project')]
        require(payload['project_id'] == data['project_id'] and payload['episode_id'] == scope, 'export project/episode mismatch')
        require(payload['source_script'] == script['path'] and payload['revision'] == script['revision'] and payload['bible_revision'] == bible['revision'], 'export source/version mismatch')
        require(payload['status'] == script['status'], 'export/script status mismatch')
    require(not output.exists(), 'bundle destination exists; refusing overwrite')
    require(output.parent.is_dir(), 'bundle parent directory must exist')
    # Keep project dependencies in the package. No filesystem paths outside root are archived.
    manifest = {'schema_version': '1.0', 'project_id': data['project_id'], 'scope': scope,
                'created_at': stamp(), 'purpose': 'script-preproduction-handoff',
                'files': {key: data['artifacts'][key] for key in sorted(selected)},
                'issues': data['issues'], 'limitation': 'Structural checks only; no claim of creative approval or recipient acceptance.'}
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('delivery-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        for key in sorted(selected):
            item = data['artifacts'][key]
            archive.write(local(root, item['path']), item['path'])
    return len(selected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init'); p.add_argument('project'); p.add_argument('--id', required=True); p.add_argument('--episodes', type=int, default=1)
    p = sub.add_parser('register'); p.add_argument('project'); p.add_argument('--id', required=True); p.add_argument('--kind', choices=sorted(KINDS), required=True); p.add_argument('--scope', default='project'); p.add_argument('--path', required=True); p.add_argument('--revision', required=True); p.add_argument('--status', choices=sorted(STATES), default='draft'); p.add_argument('--evidence'); p.add_argument('--note')
    for cmd in ['check', 'status']:
        p = sub.add_parser(cmd); p.add_argument('project')
    p = sub.add_parser('gate'); p.add_argument('project'); p.add_argument('--stage', choices=list(GATES), required=True); p.add_argument('--scope', default='project')
    p = sub.add_parser('bundle'); p.add_argument('project'); p.add_argument('--scope', required=True); p.add_argument('--output', required=True)
    p = sub.add_parser('validate-handoff'); p.add_argument('file')
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            init_project(args.project, args.id, args.episodes)
            print('INITIALIZED: blank templates only; no stage passed')
        elif args.command == 'register':
            register(args.project, args.id, args.kind, args.scope, args.path, args.revision, args.status, args.evidence, args.note)
            print('REGISTERED: metadata recorded; creative quality not inferred')
        elif args.command == 'validate-handoff':
            print(f'STRUCTURE_OK: {validate_handoff(read_json(args.file))} seconds; text parity requires review')
        elif args.command == 'bundle':
            print(f'BUNDLED: {bundle(args.project, args.scope, args.output)} artifacts; not sent to recipient')
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

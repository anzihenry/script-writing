"""Synthetic registered dependency chains; no claim of creative approval."""
from test_pipeline import p


def build(root, episodes):
    p.init_project(root, 'SCALE-FIXTURE', episodes)
    data = p.load(root)
    pairs = [(kind, 'project') for kind in ['brief', 'bible', 'outline']]
    pairs += [(kind, ep) for ep in data['episodes'] for kind in ['script', 'continuity', 'review', 'handoff']]
    for kind, scope in pairs:
        key = kind + '_' + scope
        path = root / (key + '.md')
        path.write_text('Synthetic performance fixture: ' + key, encoding='utf-8')
        deps = []
        for upstream_kind, upstream_scope in p.prerequisites(data, kind, scope):
            upstream = p.find(data, upstream_kind, upstream_scope)
            item = data['artifacts'][upstream]
            deps.append({'id': upstream, 'revision': item['revision'], 'sha256': item['sha256']})
        data['artifacts'][key] = {'kind': kind, 'scope': scope, 'path': path.name, 'revision': 'v1',
            'sha256': p.sha(path), 'status': 'reviewed' if kind in {'script', 'review'} else 'draft',
            'evidence': 'Synthetic test-only review', 'depends_on': deps}
    p.save(root, data)
    return data

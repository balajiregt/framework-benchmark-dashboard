"""Offline task/evidence preparation; deliberately has no agent or publishing adapter."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parent


def source_file(root, relative):
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or '\\' in relative:
        raise ValueError('Evidence paths must be repository-relative')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Missing or external evidence: {relative}')
    return path


def prepare(catalog, sources, output):
    if output.exists():
        raise ValueError('Output already exists; preserve the previous preparation')
    tasks = [task for task in catalog['tasks'] if not task.get('retired', False)]
    ids = [t['id'] for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate task identity')
    evidence = {project: set(paths) for project, paths in catalog['contextEvidence'].items()}
    for task in tasks:
        if task['project'] not in evidence or task['operation'] not in ('create', 'update', 'validate'):
            raise ValueError('Unknown task track or operation')
        if not task['id'].replace('-', '').isalnum():
            raise ValueError('Unsafe task identity')
        if task['sourceEditsAllowed'] != (task['operation'] != 'validate'):
            raise ValueError('Validation tasks must be read-only for source')
        if not task['request'].strip() or not task['evaluatorCriteria']:
            raise ValueError('Task requires a request and independent criteria')
        evidence[task['project']].update(task['evidence'])
    manifests = {}
    for project, paths in evidence.items():
        root = Path(sources[project]).resolve()
        # Validate all inputs before writing any output. No source files are changed.
        hashes = {p: hashlib.sha256(source_file(root, p).read_bytes()).hexdigest() for p in sorted(paths)}
        revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = bool(subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip())
        if revision != catalog['sourceRevisions'][project] or dirty:
            raise ValueError(f'{project}: use the clean inspected revision; re-review tasks for changed source')
        manifests[project] = {'revision': revision, 'workingTreeDirty': dirty, 'inspectedFileSha256': hashes}
    plan = {
        'protocol': catalog['protocol'], 'status': 'prepared-design-not-executed',
        'agentRuns': 0, 'catalogSha256': hashlib.sha256(json.dumps(catalog, sort_keys=True).encode()).hexdigest(),
        'taskCount': len(tasks), 'sources': manifests,
        'boundary': 'Task packets only; not isolated workspaces, model results or a ready execution adapter.',
        'unimplementedGates': ['isolated-projections', 'agent-tool-telemetry', 'budget-enforcement',
                              'runtime-preflight', 'independent-task-evaluators', 'workflow-public-feed'],
    }
    output.mkdir(parents=True)
    agent = output / 'agent-tasks'
    evaluator = output / 'evaluator-only'
    agent.mkdir()
    evaluator.mkdir()
    for task in tasks:
        # No evidence paths, expected classifications, criteria or source bundles in the agent prompt.
        (agent / (task['id'] + '.md')).write_text(task['request'] + '\n')
    (evaluator / 'tasks.json').write_text(json.dumps(tasks, indent=2) + '\n')
    (output / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    return plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = prepare(json.loads((ROOT / 'tasks.json').read_text()), json.loads(args.sources.read_text()), args.output.resolve())
    print(json.dumps({'status': plan['status'], 'tasksPrepared': plan['taskCount'], 'agentRuns': 0,
                      'evidenceFiles': sum(len(s['inspectedFileSha256']) for s in plan['sources'].values())}))

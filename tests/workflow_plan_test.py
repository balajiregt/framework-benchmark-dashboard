import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('workflow_prepare', ROOT / 'workflows/prepare.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class WorkflowPreparationTests(unittest.TestCase):
    def test_agent_packets_exclude_evaluator_answers_and_paths(self):
        catalog = json.loads((ROOT / 'workflows/tasks.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            for p in set(sum(catalog['contextEvidence'].values(), []) + sum([t['evidence'] for t in catalog['tasks']], [])):
                f = root / p
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text('fixture source')
            output = Path(tmp) / 'plan'
            revisions = catalog['sourceRevisions']
            with patch.object(module.subprocess, 'check_output', side_effect=[revisions['api'], '', revisions['harness'], '']):
                plan = module.prepare(catalog, {'api': str(root), 'harness': str(root)}, output)
            self.assertEqual(plan['agentRuns'], 0)
            for task in catalog['tasks']:
                packet_path = output / 'agent-tasks' / (task['id'] + '.md')
                if task.get('retired'):
                    self.assertFalse(packet_path.exists())
                    continue
                packet = packet_path.read_text()
                self.assertEqual(packet, task['request'] + '\n')
                for criterion in task['evaluatorCriteria']:
                    self.assertNotIn(criterion, packet)
            with patch.object(module.subprocess, 'check_output', side_effect=['changed-revision', '']):
                with self.assertRaisesRegex(ValueError, 're-review'):
                    module.prepare(catalog, {'api': str(root), 'harness': str(root)}, Path(tmp) / 'drifted')
            self.assertFalse((Path(tmp) / 'drifted').exists())
            with self.assertRaisesRegex(ValueError, 'already exists'):
                module.prepare(catalog, {}, output)

    def test_external_and_missing_evidence_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            root.mkdir()
            outside = Path(tmp) / 'private.txt'
            outside.write_text('private')
            (root / 'link').symlink_to(outside)
            for name in ['../private.txt', str(outside), 'link', 'missing']:
                with self.assertRaises(ValueError):
                    module.source_file(root, name)

    def test_source_write_permission_cannot_be_added_to_validation_task(self):
        catalog = json.loads((ROOT / 'workflows/tasks.json').read_text())
        next(t for t in catalog['tasks'] if t['operation'] == 'validate')['sourceEditsAllowed'] = True
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'read-only'):
                module.prepare(catalog, {}, Path(tmp) / 'plan')
            self.assertFalse((Path(tmp) / 'plan').exists())


if __name__ == '__main__':
    unittest.main()

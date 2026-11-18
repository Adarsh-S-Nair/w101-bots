"""Exercise real tracker persistence in a temporary directory, no desktop imports."""
import ast
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, List
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

path = Path(__file__).resolve().parents[2] / 'src/utils/bot_execution_tracker.py'
tree = ast.parse(path.read_text())
tree.body = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in
             ('BotExecutionTracker', 'TriviaBotTracker')]
ns = dict(json=json, os=os, datetime=datetime, timedelta=timedelta,
          Dict=Dict, Optional=Optional, Any=Any, List=List, logger=Mock())
exec(compile(tree, str(path), 'exec'), ns)
Tracker = ns['TriviaBotTracker']

class TrackerTests(unittest.TestCase):
    def test_failure_survives_reload(self):
        with TemporaryDirectory() as folder:
            tracker = Tracker(folder)
            run = tracker.start_execution()
            tracker.complete_execution(run['execution_id'], success=False)
            loaded = Tracker(folder)
            self.assertFalse(loaded.get_last_execution_info()['success'])
            self.assertEqual(loaded.get_execution_stats()['failed_executions'], 1)
            self.assertIsNone(loaded.get_next_run_time())

    def test_failure_preserves_successful_schedule(self):
        with TemporaryDirectory() as folder:
            tracker = Tracker(folder)
            run = tracker.start_execution()
            tracker.complete_execution(run['execution_id'], success=True)
            scheduled = tracker.get_next_run_time()
            run = tracker.start_execution()
            tracker.complete_execution(run['execution_id'], success=False)
            loaded = Tracker(folder)
            self.assertEqual(loaded.get_next_run_time(), scheduled)
            self.assertTrue(loaded.tracking_data['last_successful_execution']['success'])
            self.assertEqual(len(loaded.get_execution_history()), 2)

    def test_legacy_success_schedule_preserved(self):
        with TemporaryDirectory() as folder:
            tracker = Tracker(folder)
            tracker.tracking_data = {'last_execution': {'success': True, 'next_run_time':
                {'iso': '2026-12-01T12:00:00'}}}
            run = tracker.start_execution()
            tracker.complete_execution(run['execution_id'], success=False)
            self.assertEqual(Tracker(folder).get_next_run_time(), datetime(2026,12,1,12))

    def test_write_error_is_not_success(self):
        with TemporaryDirectory() as folder:
            tracker = Tracker(folder)
            run = tracker.start_execution()
            tracker._save_tracking_data = Mock(return_value=False)
            with self.assertRaises(OSError):
                tracker.complete_execution(run['execution_id'], success=True)

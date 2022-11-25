"""
Test custom django management commands
"""
from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
class CommandsTests(SimpleTestCase):
    """
    Test commands
    """

    def test_wait_for_db_ready(self, patched_check):
        """
        Test waiting for db when db is available
        """
        patched_check.return_value = True
        call_command('wait_for_db')
        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_not_ready(self, patched_sleep, patched_check):
        """
        Test waiting for db when db is not available
        """
        patched_check.side_effect = [Psycopg2Error] * 2 + \
            [OperationalError] * 2 + [True]
        call_command('wait_for_db')
        self.assertEqual(patched_check.call_count, 5)
        patched_check.assert_called_with(databases=['default'])

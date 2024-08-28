import sys
import os
from io import StringIO
from unittest import TestCase
from mock import patch
from pathlib import Path

path = Path(os.path.dirname(os.path.abspath(__file__)))
parts = list(path.parts)
parts[path.parts.index('tests')] = "image_content"
target_path = Path(*parts).absolute()
sys.path.append(str(target_path))

class testlogger(TestCase):

    def setUp(self):
        self.target = __import__('k8shealthcheck')
        self.logger = __import__('logger')
        self.info_log_prefix = self.logger.BOLD + self.logger.BLUE + self.logger.INFO
        self.warning_log_prefix = self.logger.BOLD + self.logger.YELLOW + \
                                        self.logger.WARNING
        self.error_log_prefix = self.logger.BOLD + self.logger.RED + self.logger.ERROR
        self.print_log_suffix = self.logger.END + self.logger.END

    @patch('sys.stdout', new_callable=StringIO)
    def test_error_to_print_error(self, mock_out):
        input_message = 'error message'
        expected_output = self.error_log_prefix + input_message + self.print_log_suffix
        self.logger.LogLevel.error(input_message)
        self.assertEqual(mock_out.getvalue().strip(), expected_output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_warning_to_print_warning(self, mock_out):
        input_message = 'warning message'
        expected_output = self.warning_log_prefix + input_message + self.print_log_suffix
        self.logger.LogLevel.warning(input_message)
        self.assertEqual(mock_out.getvalue().strip(), expected_output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_info_to_print_info(self, mock_out):
        input_message = 'info message'
        expected_output = self.info_log_prefix + input_message + self.print_log_suffix
        self.logger.LogLevel.info(input_message)
        self.assertEqual(mock_out.getvalue().strip(), expected_output)

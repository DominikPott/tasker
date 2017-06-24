import unittest
from tasker.control import get_asset_task_templates

class ControlTestCase(unittest.TestCase):
    """Test for control.py."""

    def test_get_asset_task_templates(self):
        """Is the correct template choosen"""
        self.assertFalse(get_asset_task_templates())

if __name__ == '__main__':
    unittest.main()
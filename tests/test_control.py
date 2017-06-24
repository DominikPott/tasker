import unittest
from tasker.control import get_task_templates_by_category_name

class ControlTestCase(unittest.TestCase):
    """Test for control.py."""

    def test_get_asset_task_templates(self):
        """Is a template choosen and returned"""
        self.assertTrue(get_task_templates_by_category_name('shot'))

if __name__ == '__main__':
    unittest.main()
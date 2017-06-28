import unittest
from tasker.control import get_task_templates_by_category_name


class ControlTestCase(unittest.TestCase):
    """Test for control.py."""

    def test_get_asset_task_templates(self):
        """Is a template choosen and returned"""
        self.assertTrue(get_task_templates_by_category_name('asset'))

    def test_get_template_for_number_raises_KeyError(self):
        """Test if wrong template query raises a KeyError"""
        self.assertRaises(KeyError, get_task_templates_by_category_name, 10)

if __name__ == '__main__':
    unittest.main()
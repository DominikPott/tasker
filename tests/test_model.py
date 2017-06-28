import unittest
from tasker.model import State


class ModelTestCase(unittest.TestCase):
    """Tests for 'model.py' to garanty correct data strucktures."""

    def test_done_state_exists(self):
        """Test if done state is defined."""
        self.assertEqual(State.done, 'done')

    def test_pending_state_exists(self):
        """Test if pending state is defined."""
        self.assertEqual(State.pending, 'pending on other tasks')

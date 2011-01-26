from layers.tests import *

class TestMainController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='main', action='index'))
        # Test response...

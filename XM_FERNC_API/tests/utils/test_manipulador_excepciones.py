import unittest

from utils.manipulador_excepciones import ManipuladorExcepciones


class TestManipuladorExcepciones(unittest.TestCase):
    def setUp(self):
        self.manipulador = ManipuladorExcepciones("Test error", "Mensaje tarea test", "Mensaje error test")

    def test_obtener_error(self):
        self.assertEqual(self.manipulador.obtener_error(), "Test error")

    def test_obtener_mensaje_tarea(self):
        self.assertEqual(self.manipulador.obtener_mensaje_tarea(), "Mensaje tarea test")
    
    def test_obtener_mensaje_error(self):
        self.assertEqual(self.manipulador.obtener_mensaje_error(), "Mensaje error test")

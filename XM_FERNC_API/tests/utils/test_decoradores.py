import unittest
from unittest.mock import MagicMock

from utils.decoradores import capturar_excepciones
from utils.manipulador_excepciones import BaseExcepcion


class TestCapturarExcepciones(unittest.TestCase):

    def test_captura_excepcion_base_excepcion(self):
        """Prueba que el decorador capture una BaseException y la vuelva a lanzar."""

        class MiExcepcion(BaseExcepcion):
            pass

        @capturar_excepciones("Tarea de prueba", "Mensaje de prueba", MiExcepcion)
        def mi_funcion(arg1, arg2):
            raise MiExcepcion("Error simulado")

        with self.assertRaises(MiExcepcion):
            mi_funcion(1, 2)

    def test_captura_excepcion_otra_excepcion(self):
        """Prueba que el decorador capture otras excepciones y genere una personalizada."""

        resultado_esperado = (
            KeyError("Clave no encontrada"),
            "Tarea de prueba",
            "Mensaje de prueba",
        )

        @capturar_excepciones("Tarea de prueba", "Mensaje de prueba", ValueError)
        def funcion_test(arg1, arg2):
            raise KeyError("Clave no encontrada")

        with self.assertRaises(ValueError) as error:
            funcion_test(1, 2)

        self.assertEqual(error.exception.args[0].args[0], resultado_esperado[0].args[0])

        for res, esp in zip(error.exception.args[1:], resultado_esperado[1:]):
            self.assertEqual(res, esp)

    def test_funcion_sin_excepcion(self):
        """Prueba que el decorador pasa a traves del resultado si no hay excepcion."""

        @capturar_excepciones("Tarea de prueba", "Mensaje de prueba", Exception)
        def mi_funcion(arg1, arg2):
            return arg1 + arg2

        resultado = mi_funcion(3, 5)
        self.assertEqual(resultado, 8)

    def test_mock_impresion(self):
        """Prueba que el decorador imprime un error usando un mock."""

        funcion_mock = MagicMock()
        funcion_mock.side_effect = KeyError("Clave no encontrada")

        decorada = capturar_excepciones(
            "Tarea de prueba", "Mensaje de prueba", Exception
        )(funcion_mock)

        with self.assertRaises(Exception):
            decorada(1, 2)

        self.assertTrue(funcion_mock.called)
        funcion_mock.assert_called_once_with(1, 2)

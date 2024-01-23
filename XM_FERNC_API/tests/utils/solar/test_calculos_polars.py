import unittest
import pytest
from utils.solar.calculos_polars import calculo_dhi, calculo_temp_panel


class TestCalculosPolars(unittest.TestCase):
    def test_calculo_dhi(self):
        """
        Prueba el cálculo de DHI.

        Esta función prueba el cálculo de la Irradiancia Horizontal Difusa (DHI).
        Compara el resultado calculado con el resultado esperado utilizando el método pytest.approx.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None
        """
        struct = [0.30, 0.65, 119.236]  # Test input
        resultado_esperado = 0.617465223348021

        resultado = calculo_dhi(struct)

        # Asegura que el resultado es approximado al resultado esperado
        assert resultado_esperado == pytest.approx(resultado)

    def test_calculo_temp_panel(self):
        """
        Prueba el cálculo de la temperatura del panel.

        Esta función prueba el cálculo de la temperatura del panel.
        Compara el resultado calculado con el resultado esperado utilizando el método pytest.approx.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None
        """
        struct = [657.430433, 26.49, 45]  # Test input
        resultado_esperado = 47.034701031249995

        resultado = calculo_temp_panel(struct)

        # Asegura que el resultado es approximado al resultado esperado
        assert resultado_esperado == pytest.approx(resultado)

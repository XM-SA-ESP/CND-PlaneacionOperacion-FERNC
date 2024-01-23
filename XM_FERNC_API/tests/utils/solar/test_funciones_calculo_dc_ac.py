import unittest
import pandas as pd
import pandas.testing as pdt

from unittest import mock
from pvlib.pvsystem import PVSystem

from utils.solar.funciones_calculo_dc_ac import CalculoDCAC


class TestCalculoDCAC(unittest.TestCase):
    def setUp(self) -> None:
        self.calculo_dc_ac_instancia = CalculoDCAC()

    # def test_calculo_potencia_dc_ac(self):

    #     mock_params_modulo = mock.MagicMock()
    #     mock_params_inv = mock.MagicMock()
    #     mock_params_trans = mock.MagicMock()
    #     mock_pvsys = mock.MagicMock()
    #     mock_lista_array = mock.MagicMock()

    #     series_esperada = pd.Series([0, 99, 0, 77])

    #     with mock.patch.object(self.calculo_dc_ac_instancia, 'calculo_potencia_dc') as mock_calculo_potencia_dc, \
    #             mock.patch.object(self.calculo_dc_ac_instancia, 'calculo_potencia_ac') as mock_calculo_potencia_ac, \
    #             mock.patch.object(self.calculo_dc_ac_instancia, "ajuste_potencia_con_ihf_perdidas") as mock_ihf_perdidas:

    #         mock_ihf_perdidas.return_value = pd.Series([-33, 99, -66, 77])

    #         resultado = self.calculo_dc_ac_instancia.calculo_potencia_dc_ac(
    #             pvsys=mock_pvsys,
    #             lista_array=mock_lista_array,
    #             params_trans=mock_params_trans,
    #             params_inversor=mock_params_inv,
    #             params_modulo=mock_params_modulo
    #         )

    #         mock_calculo_potencia_dc.assert_called()
    #         mock_calculo_potencia_ac.assert_called()
    #         # mock_ihf_perdidas.assert_called()

    #         pd.testing.assert_series_equal(resultado, series_esperada)

    # # @mock.patch("pvlib.pvsystem.PVSystem.scale_voltage_current_power")
    # def test_calculo_potencia_dc(self):
    #     pvsys = PVSystem()
    #     params_trans = mock.MagicMock()
    #     params_mod = mock.MagicMock()

    #     params_trans.Ihf = 87.0
    #     params_trans.L = 14.0
    #     params_mod.Psi = 10.0
    #     mock_lista_array = pd.DataFrame({
    #         'v_mp': [20, 25, 30],
    #         'v_oc': [25, 30, 35],
    #         'i_mp': [5, 6, 7],
    #         'i_x': [1, 1.2, 1.4],
    #         'i_xx': [0.9, 1, 1.1],
    #         'i_sc': [8, 9, 10],
    #         'p_mp': [100, 150, 200]
    #     })

    #     mock_data = {
    #         "solucion_cec": pd.DataFrame({"i_mp": [1, 2, 3], "p_mp": [10, 20, 30]})
    #     }

    #     df_esperado = pd.DataFrame(
    #         {"i_mp": [0.774, 1.548, 2.322], "p_mp": [7.74, 15.48, 23.22]}
    #     )

    #     # Configura el valor de retorno del mock para ser una instancia de PVSystem
    #     # pvsys_scale_mock.return_value = PVSystem()

    #     resultado = self.calculo_dc_ac_instancia.calculo_potencia_dc(
    #         pvsys, mock_lista_array, params_trans, params_mod
    #     )

    #     pd.testing.assert_frame_equal(resultado, df_esperado)

    def test_calculo_potencia_ac(self):
        mock_params_inv = mock.MagicMock()
        mock_params_inv.PACnominal = 200000.0
        mock_params_inv.PDCnominal = 202507.04
        mock_params_inv.VDCnominal = 1174.0
        mock_params_inv.PDCarranque = 2025.07
        mock_params_inv.PACnocturnoW = 3.3
        mock_params_inv.PowerDc = [12, 13, 12, 12, 15, 12, 12,
                                   12, 12, 12, 12, 12, 18, 12, 12, 12, 17, 12, 12, 19, 12]
        mock_params_inv.PowerAc = [12, 12, 12, 12, 27, 12, 12,
                                   12, 24, 12, 12, 12, 12, 12, 12, 12, 28, 12, 26, 12, 12]

        df1 = pd.DataFrame({
            'v_mp': [20, 25, 30],
            'p_mp': [100, 150, 200]
        })

        df2 = pd.DataFrame({
            'v_mp': [22, 27, 32],
            'p_mp': [110, 160, 210]
        })

        lista = [df1, df2]

        serie_esperada = pd.Series(
            [0.0,0.0,0.0], name="p_ac"
        )

        resultado = self.calculo_dc_ac_instancia.calculo_potencia_ac(
            lista, mock_params_inv
        )

        pd.testing.assert_series_equal(resultado, serie_esperada)

    def test_ajuste_potencia_perdidas(self):
        df = pd.DataFrame({"i_mp": [1, 2, 3], "p_mp": [10, 20, 30]})
        psi = 0.1
        l = 0.2

        df_esperado = pd.DataFrame(
            {
                "i_mp": [0.9970019999999999, 1.9940039999999999, 2.991006],
                "p_mp": [9.97002, 19.94004, 29.910059999999998],
            }
        )

        resultado = self.calculo_dc_ac_instancia.ajuste_potencia_perdidas(
            df, psi, l)

        pdt.assert_frame_equal(df_esperado, resultado)

    def test_ajuste_potencia_con_ihf_perdidas(self):
        # Create test data
        series = pd.Series(
            [
                143414.794357,
                202507.040000,
                202507.040000,
            ],
            index=[
                pd.Timestamp("2008-01-01 00:00:00-0500", tz="America/Bogota"),
                pd.Timestamp("2008-01-01 01:00:00-0500", tz="America/Bogota"),
                pd.Timestamp("2008-01-01 02:00:00-0500", tz="America/Bogota"),
            ],
            name="p_ac",
        )

        mock_params_trans = mock.MagicMock()
        mock_params_trans.Ihf = 87.0
        mock_params_trans.Kpc = 1
        mock_params_trans.Kt = 1
        mock_params_trans.Kin = 1

        result = self.calculo_dc_ac_instancia.ajuste_potencia_con_ihf_perdidas(
            series, mock_params_trans
        )

        expected_result = pd.Series(
            [-11967349.913283037, -16898344.54282656, -16898344.54282656],
            index=[
                pd.Timestamp("2008-01-01 00:00:00-0500", tz="America/Bogota"),
                pd.Timestamp("2008-01-01 01:00:00-0500", tz="America/Bogota"),
                pd.Timestamp("2008-01-01 02:00:00-0500", tz="America/Bogota"),
            ],
            name="p_ac",
        )
        pd.testing.assert_series_equal(result, expected_result)

    def test_obtener_energia(self):
        # Preparar datos de entrada
        series1 = pd.Series([1000, 2000, 3000], name="serie1")  # en Wh
        series2 = pd.Series([2000, 3000, 4000], name="serie2")  # en Wh
        lista_series = [series1, series2]

        # Llamar al método que estamos probando
        resultado = self.calculo_dc_ac_instancia.obtener_energia(lista_series)

        # Calcular el resultado esperado
        resultado_esperado = pd.Series(
            [3.0, 5.0, 7.0], name="energia_kWh")  # en kWh

        # Comprobar que el resultado es correcto
        pdt.assert_series_equal(resultado, resultado_esperado)

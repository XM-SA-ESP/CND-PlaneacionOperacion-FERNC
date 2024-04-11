import unittest
import pandas as pd
import pandas.testing as pdt

from unittest import mock
from xm_solarlib.pvsystem import PVSystem
from infraestructura.models.solar.parametros import ParametrosInversor

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

    # # @mock.patch("xm_solarlib.pvsystem.PVSystem.scale_voltage_current_power")
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

        data_json = {
            "CurvaPDCVSPACEnVDCMax": [
                {"Id": 1.0, "XVdcmax": 89060.0, "YVdcmax": 84437.8},
                {"Id": 2.0, "XVdcmax": 174070.0, "YVdcmax": 168865.3},
                {"Id": 3.0, "XVdcmax": 344670.0, "YVdcmax": 337742.1},
                {"Id": 4.0, "XVdcmax": 515210.0, "YVdcmax": 506606.0},
                {"Id": 5.0, "XVdcmax": 857730.0, "YVdcmax": 844349.4},
                {"Id": 6.0, "XVdcmax": 1286600.0, "YVdcmax": 1266529.0},
                {"Id": 7.0, "XVdcmax": 1716860.0, "YVdcmax": 1688703.5},
            ],
            "CurvaPDCVSPACEnVDCMin": [
                {"Id": 1.0, "XVdcMin": 87520.0, "YVdcMin": 84439.3},
                {"Id": 2.0, "XVdcMin": 172720.0, "YVdcMin": 168868.3},
                {"Id": 3.0, "XVdcMin": 343090.0, "YVdcMin": 337737.8},
                {"Id": 4.0, "XVdcMin": 513280.0, "YVdcMin": 506607.4},
                {"Id": 5.0, "XVdcMin": 854520.0, "YVdcMin": 844351.2},
                {"Id": 6.0, "XVdcMin": 1282560.0, "YVdcMin": 1266528.0},
                {"Id": 7.0, "XVdcMin": 1712680.0, "YVdcMin": 1688702.5},
            ],
            "CurvaPDCVSPACEnVDCNominal": [
                {"Id": 1.0, "XVdcnominal": 88160.0, "YVdcnominal": 84439.6},
                {"Id": 2.0, "XVdcnominal": 173310.0, "YVdcnominal": 168873.3},
                {"Id": 3.0, "XVdcnominal": 343860.0, "YVdcnominal": 337739.3},
                {"Id": 4.0, "XVdcnominal": 515790.0, "YVdcnominal": 508001.6},
                {"Id": 5.0, "XVdcnominal": 856510.0, "YVdcnominal": 844347.6},
                {"Id": 6.0, "XVdcnominal": 1285160.0, "YVdcnominal": 1266525.2},
                {"Id": 7.0, "XVdcnominal": 1715980.0, "YVdcnominal": 1688695.9},
            ],
            "NInv": 4,
            "PACnocturnoW": 3.3,
            "PACnominal": 200000.0,
            "PDCarranque": 2025.07,
            "PDCnominal": 202507.04,
            "PowerAc": [
                84439.3,
                168868.3,
                337737.8,
                506607.4,
                844351.2,
                1266528.0,
                1688702.5,
                84439.6,
                168873.3,
                337739.3,
                508001.6,
                844347.6,
                1266525.2,
                1688695.9,
                84437.8,
                168865.3,
                337742.1,
                506606.0,
                844349.4,
                1266529.0,
                1688703.5,
            ],
            "PowerDc": [
                87520.0,
                172720.0,
                343090.0,
                513280.0,
                854520.0,
                1282560.0,
                1712680.0,
                88160.0,
                173310.0,
                343860.0,
                515790.0,
                856510.0,
                1285160.0,
                1715980.0,
                89060.0,
                174070.0,
                344670.0,
                515210.0,
                857730.0,
                1286600.0,
                1716860.0,
            ],
            "ReferenciaInversor": "inv 001",
            "VDCnominal": 1174.0,
        }

        para_inv = ParametrosInversor.model_validate(data_json)

        df1 = pd.DataFrame({"v_mp": [20, 25, 30], "p_mp": [100, 150, 200]})

        df2 = pd.DataFrame({"v_mp": [22, 27, 32], "p_mp": [110, 160, 210]})

        lista = [df1, df2]

        serie_esperada = pd.Series([0.0, 0.0, 0.0], name="p_ac")

        resultado = self.calculo_dc_ac_instancia.calculo_potencia_ac(lista, para_inv)

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

import json
import polars as pl
import pandas as pd
import numpy as np
import pandas.testing as pdt
from xm_solarlib.pvsystem import PVSystem
from pandas import DataFrame
from typing import Dict
from unittest import TestCase, mock
from unittest.mock import MagicMock, Mock, patch
from dominio.servicio.solar.servicio_solares import ServicioSolar
from infraestructura.models.respuesta import Respuesta, Resultado
from infraestructura.models.solar.parametros import (
    JsonModelSolar,
    ParametrosTransversales,
    ParametrosInversor,
    ParametrosModulo,
)
from dominio.servicio.azure_blob.cliente_azure import ClienteAzure
from tests.dominio.servicio.azure_blob.test_cliente_azure import MockClienteAzure


class TestServicioSolar(TestCase):
    def setUp(self):
        """
        Configura el entorno de prueba para el caso de prueba.

        Esta función inicializa los objetos y datos necesarios para el caso de prueba.
        Crea una instancia simulada de la clase `ServicioSolar` y la asigna a `self.servicio_solar_mock`.
        Crea una instancia de la clase `ServicioSolar` y la asigna a `self.servicio_solar_instancia`.
        Carga los resultados esperados de los archivos de datos de prueba y los asigna a las variables correspondientes.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None
        """

        # Creacion de una instancia Mock de ServicioSolar
        self.servicio_solar_mock = mock.Mock(spec=ServicioSolar)
        self.servicio_solar = self.servicio_solar_mock

        # Creacion Instancia ServicioSolar
        self.servicio_solar_instancia = ServicioSolar()

        # Carga de los resultados esperados
        data = "./tests/data/test_dataframe.parquet"
        self.df = pl.read_parquet(data)
        self.df_pd = pd.read_parquet(data)

    def test_ejecutar_calculo_dni_dhi(self):
        # Crear un MagickMock de DataFrame y JsonModel
        mock_df = mock.MagicMock()
        mock_params = mock.MagicMock()

        # Parchear los metodos que se usan en ejecutar_calculo_dni_dhi
        with mock.patch.object(
            self.servicio_solar_instancia.manipulador_df, "crear_serie_doy"
        ) as mock_crear_serie_doy, mock.patch.object(
            self.servicio_solar_instancia.calculo_dni_dhi, "obtener_localizacion"
        ) as mock_obtener_localizacion, mock.patch.object(
            self.servicio_solar_instancia.calculo_dni_dhi, "obtener_angulo_zenital"
        ) as mock_obtener_angulo_zenital, mock.patch.object(
            self.servicio_solar_instancia.calculo_dni_dhi,
            "obtener_irradiacion_extraterrestre",
        ) as mock_obtener_irradiacion_extraterrestre, mock.patch.object(
            self.servicio_solar_instancia.manipulador_df, "crear_df_calculo_dni"
        ) as mock_crear_df_calculo_dni, mock.patch.object(
            self.servicio_solar_instancia.calculo_dni_dhi, "obtener_dni"
        ) as mock_obtener_dni, mock.patch.object(
            self.servicio_solar_instancia.calculo_dni_dhi, "obtener_dhi"
        ) as mock_obtener_dhi, mock.patch.object(
            self.servicio_solar_instancia.manipulador_df, "combinar_dataframes"
        ) as mock_combinar_dataframes:
            self.servicio_solar_instancia.ejecutar_calculo_dni_dhi(mock_df, mock_params)

            # Asegurar que los demas metodo fueron llamados
            mock_crear_serie_doy.assert_called_once_with(
                mock_df, mock_params.ParametrosTransversales.ZonaHoraria
            )
            mock_obtener_localizacion.assert_called_once_with(
                mock_params.ParametrosTransversales.Latitud,
                mock_params.ParametrosTransversales.Longitud,
                mock_params.ParametrosTransversales.ZonaHoraria,
                mock_params.ParametrosTransversales.Altitud,
            )
            mock_obtener_angulo_zenital.assert_called_once_with(
                mock_obtener_localizacion.return_value,
                mock_crear_serie_doy.return_value,
            )
            mock_obtener_irradiacion_extraterrestre.assert_called_once_with(
                mock_crear_serie_doy.return_value
            )
            mock_crear_df_calculo_dni.assert_called_once_with(
                mock_obtener_angulo_zenital.return_value,
                mock_obtener_irradiacion_extraterrestre.return_value,
                mock_df,
            )
            mock_obtener_dni.assert_called_once_with(
                mock_crear_df_calculo_dni.return_value
            )
            mock_obtener_dhi.assert_called_once_with(
                mock_obtener_dni.return_value, mock_crear_df_calculo_dni.return_value
            )
            mock_combinar_dataframes.assert_called_once_with(
                mock_obtener_dhi.return_value,
                mock_obtener_angulo_zenital.return_value,
                mock_obtener_irradiacion_extraterrestre.return_value,
            )

    # def test_ejecutar_calculos(self):
    #     # Crear un MagickMock de DataFrame y JsonModel
    #     mock_df = mock.MagicMock()
    #     mock_params = mock.MagicMock()

    #     self.servicio_solar_instancia.cliente_azure = mock.MagicMock()

    #     # Parchear los metodos que se usan en ejecutar_calculos
    #     with mock.patch.object(self.servicio_solar_instancia, 'ejecutar_calculo_temperatura_panel') as mock_ejecutar_calculo_temp_panel, \
    #         mock.patch.object(self.servicio_solar_instancia.manipulador_df, 'filtrar_dataframe') as mock_filtar_df, \
    #         mock.patch.object(self.servicio_solar_instancia.manipulador_df, 'restaurar_dataframe') as mock_restaurar_df, \
    #         mock.patch.object(self.servicio_solar_instancia, 'ejecutar_calculo_dni_dhi') as mock_ejecutar_calculo_dni_dhi, \
    #         mock.patch.object(self.servicio_solar_instancia, 'ejecutar_calculo_poa') as mock_ejecutar_calculo_poa, \
    #         mock.patch.object(self.servicio_solar_instancia, 'ejecutar_calculo_dc_ac') as mock_calculo_dc_ac, \
    #         mock.patch.object(self.servicio_solar_instancia, 'ejecutar_calculo_energia') as mock_calculo_energia, \
    #         mock.patch.object(self.servicio_solar_instancia.manipulador_df, 'filtrar_por_mes') as mock_filtrar_por_mes, \
    #         mock.patch.object(self.servicio_solar_instancia.manipulador_df, 'filtrar_por_dia') as mock_filtrar_por_dia, \
    #         mock.patch.object(self.servicio_solar_instancia.cliente_azure, 'archivo_subir') as mock_archivo_subir:

    #         # Mockear los resultados de los demas metodos
    #         mock_ejecutar_calculo_dni_dhi.return_value = mock.MagicMock()
    #         mock_ejecutar_calculo_poa.return_value = (mock.MagicMock(), mock.MagicMock())

    #         self.servicio_solar_instancia.ejecutar_calculos(mock_df, mock_params)

    #         # Asegurar que los demas metodo fueron llamados
    #         mock_ejecutar_calculo_temp_panel.assert_called_once()
    #         mock_ejecutar_calculo_dni_dhi.assert_called_once()
    #         mock_filtar_df.assert_called_once()
    #         mock_ejecutar_calculo_poa.assert_called_once()
    #         mock_restaurar_df.assert_called_once()
    #         mock_calculo_dc_ac.assert_called_once()
    #         mock_calculo_energia.assert_called_once()
    #         mock_filtrar_por_mes.assert_called_once()
    #         mock_filtrar_por_dia.assert_called_once()
    #         mock_archivo_subir.call_count == 2

    def test_ejecutar_calculo_poa(self):
        """
        Prueba el método 'ejecutar_calculo_poa' de la clase ServicioSolar.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None
        """
        df_dni_dhi = pd.DataFrame(
            {
                "azimuth": [100, 120, 140],
                "zenith": [30, 40, 50],
                "dni": [800, 900, 1000],
                "dhi": [100, 200, 300],
                "iext": [1.1, 1.2, 1.3],
                "airmass": [1.0, 1.1, 1.2],
                "ghi [Wh/m2]": [500, 600, 700],
                "apparent_zenith": [1, 2, 3],
            }
        )

        with open("./tests/data/test_json_data.json") as f:
            json_data = json.load(f)
        params = JsonModelSolar(**json_data)
        resultado_esperado = pd.DataFrame(
            {"poa": [942.1393462493, 1146.9315380012, 1247.9103501709]}
        )
        (
            inversores_pvsystem,
            inversores_resultados,
        ) = self.servicio_solar_instancia.ejecutar_calculo_poa(df_dni_dhi, params)
        df_resultado = inversores_resultados["Inversor 1 Array 1 POA"]["POA"]

        # Asegurar que los resultados sean diccionarios
        self.assertIsInstance(inversores_pvsystem, Dict)
        self.assertIsInstance(inversores_resultados, Dict)
        pdt.assert_frame_equal(df_resultado, resultado_esperado)

    def test_ejecutar_calculo_temperatura_panel(self):
        df_series = pd.DataFrame({"Ta": [20, 25, 30]})
        df_dhi_dni = pd.DataFrame({"index": [1, 2, 3]})
        mock_params_inv = mock.MagicMock()
        mock_params_inv.ParametrosModulo.Tnoct = 45

        # Dicionario de data mock para el calculo
        self.servicio_solar_instancia.inversores_resultados = {
            "data1": {
                "POA": pd.DataFrame(
                    {"poa": [657.43, 1020.06, 955.41], "Ta": [20, 25, 30]}
                ),
                "params_inv": mock_params_inv,
                "params_array": mock.MagicMock(),
            },
            "data2": {
                "POA": pd.DataFrame(
                    {"poa": [651.04, 1007.45, 941.01], "Ta": [20, 25, 30]}
                ),
                "params_inv": mock_params_inv,
                "params_array": mock.MagicMock(),
            },
        }

        # Llamado al metodo
        self.servicio_solar_instancia.ejecutar_calculo_temperatura_panel()

        # Asegurar que la columna temp_panel fue agregada a la instancia.
        self.assertIn(
            "temp_panel",
            self.servicio_solar_instancia.inversores_resultados["data1"]["POA"].columns,
        )
        self.assertIn(
            "temp_panel",
            self.servicio_solar_instancia.inversores_resultados["data2"]["POA"].columns,
        )

        # Asegurar que los valores de fueron calculados correctamente.
        expected_temp_panel_data1 = pd.Series(
            [40.544687, 56.876875, 59.856562], name="temp_panel"
        )
        expected_temp_panel_data2 = pd.Series(
            [40.345000, 56.482813, 59.406562], name="temp_panel"
        )

        pd.testing.assert_series_equal(
            self.servicio_solar_instancia.inversores_resultados["data1"]["POA"][
                "temp_panel"
            ],
            pd.Series(expected_temp_panel_data1),
        )
        pd.testing.assert_series_equal(
            self.servicio_solar_instancia.inversores_resultados["data2"]["POA"][
                "temp_panel"
            ],
            pd.Series(expected_temp_panel_data2),
        )

    @mock.patch("xm_solarlib.irradiance.get_total_irradiance")
    @mock.patch("xm_solarlib.bifacial.pvfactors.pvfactors_timeseries")
    def test_calculo_poa_con_seguidores_y_bifacial(
        self, mock_pvfactors_timeseries, mock_irradiance
    ):
        # Crear data mock
        df_dni_dhi = pd.DataFrame(
            {
                "azimuth": [100, 120, 140],
                "zenith": [30, 40, 50],
                "dni": [800, 900, 1000],
                "dhi": [100, 200, 300],
                "iext": [1.1, 1.2, 1.3],
                "apparent_zenith": [1, 2, 3],
            }
        )

        montura = mock.MagicMock()
        params_trans = mock.MagicMock()
        params_inv = mock.MagicMock()
        params_array = mock.MagicMock()
        params_inv.ParametrosModulo.Bifacial = True
        params_inv.ParametrosModulo.Bifacialidad = 0.7

        # Configurar valores mock esperados
        mock_pvfactors_timeseries.return_value = pd.DataFrame(
            {
                "total_inc_front": [1, 2, 3],
                "total_inc_back": [1, 2, 3],
            },
            index=df_dni_dhi.index,
        ).transpose()

        df_esperado = pd.DataFrame({"poa": [1.7, 3.4, 5.1]})

        # Llamado al metodo
        result = self.servicio_solar_instancia.calculo_poa(
            df_dni_dhi, montura, params_trans, params_inv, params_array
        )

        # Asegurar el output esperado
        self.assertIsInstance(result, pd.DataFrame)

        # Asegurar que el metodo fue llamado como se espera
        mock_pvfactors_timeseries.assert_called_once()
        mock_irradiance.assert_not_called()
        self.assertEqual(result.columns, ["poa"])

        # Asegurar el dataframe esperado
        pdt.assert_frame_equal(result, df_esperado)

    @mock.patch("xm_solarlib.bifacial.pvfactors.pvfactors_timeseries")
    @mock.patch("xm_solarlib.irradiance.get_total_irradiance")
    def test_calculo_poa_sin_seguidores_and_no_bifacial(
        self, mock_get_total_irradiance, mock_pvfactors_timeseries
    ):
        # Crear data mock
        df_dni_dhi = pd.DataFrame(
            {
                "azimuth": [100, 120, 140],
                "zenith": [30, 40, 50],
                "dni": [800, 900, 1000],
                "dhi": [100, 200, 300],
                "iext": [1.1, 1.2, 1.3],
                "airmass": [1.0, 1.1, 1.2],
                "ghi [Wh/m2]": [500, 600, 700],
            }
        )
        montura = mock.MagicMock()
        params_trans = mock.MagicMock()
        params_inv = mock.MagicMock()
        params_array = mock.MagicMock()
        params_inv.ParametrosModulo.Bifacial = False

        # Configurar valores mock esperados
        mock_get_total_irradiance.return_value = pd.DataFrame(
            {"poa_global": [1, 2, 3]}, index=df_dni_dhi.index
        )

        expected_shape = mock_get_total_irradiance.return_value.shape

        # Llamado al metodo
        result = self.servicio_solar_instancia.calculo_poa(
            df_dni_dhi, montura, params_trans, params_inv, params_array
        )

        df_esperado = pd.DataFrame({"poa": [1, 2, 3]})

        # Asegurar el output esperado
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.shape, expected_shape)

        # Asegurar que el metodo fue llamado como se espera
        mock_get_total_irradiance.assert_called_once()
        mock_pvfactors_timeseries.assert_not_called()
        self.assertEqual(result.columns, ["poa"])

        # Asegurar el dataframe esperado
        pdt.assert_frame_equal(result, df_esperado)

    @mock.patch("xm_solarlib.ivtools.sdm.fit_cec_sam")
    @mock.patch("xm_solarlib.pvsystem.calcparams_cec")
    def test_ejecutar_calculo_parametros_cec(
        self, mock_obtener_parametros_circuito_eq, mock_obtener_parametros_fit_cec_sam
    ):
        # Crear data mock
        self.servicio_solar_instancia.inversores_resultados = {
            "data": {
                "POA": pd.DataFrame(
                    {"poa": [657.43, 1020.06, 955.41], "temp_panel": [1, 2, 3]}
                ),
                "params_inv": mock.MagicMock(),
                "params_array": mock.MagicMock(),
            },
        }
        columnas_esperadas = [
            "photocurrent",
            "saturation_current",
            "resistance_series",
            "resistance_shunt",
            "nNsVth",
        ]

        # Valores que retornaran las funciones usadas en el metodo
        mock_obtener_parametros_fit_cec_sam.return_value = (1, 2, 3, 4, 5, 6)
        mock_obtener_parametros_circuito_eq.return_value = pd.DataFrame([1, 2, 3, 4, 5])

        # Llamado al metodo
        self.servicio_solar_instancia.ejecutar_calculo_parametros_cec()

        # Columnas espereadas y generadas por el metodo
        columnas_esperadas = [
            "photocurrent",
            "saturation_current",
            "resistance_series",
            "resistance_shunt",
            "nNsVth",
        ]
        columnas_resultados = self.servicio_solar_instancia.inversores_resultados[
            "data"
        ]["params_cec"].columns

        # Asegurar que los llamados fueron hechos
        mock_obtener_parametros_fit_cec_sam.assert_called_once()
        mock_obtener_parametros_circuito_eq.assert_called_once()

        # Asegurar que las columnas generadas son las columnas esperadas
        assert all([col in columnas_resultados for col in columnas_esperadas])

    def test_ejecutar_calculo_solucion_cec(self):
        self.servicio_solar_instancia.inversores_resultados = {
            "data": {
                "POA": pd.DataFrame(
                    {"poa": [1, 2, 3]},
                    index=pd.to_datetime(
                        ["09:00", "12:00", "18:00"], format="%H:%M"
                    ).tz_localize("America/Bogota"),
                ),
                "params_cec": pd.DataFrame(
                    {
                        "photocurrent": [0.0, 0.0, 0.0],
                        "saturation_current": [
                            9.388082e-11,
                            8.620696e-11,
                            7.879565e-11,
                        ],
                        "resistance_series": [100.64, 100.64, 100.64],
                        "resistance_shunt": [np.inf, np.inf, np.inf],
                        "nNsVth": [1.941, 1.937, 1.933],
                    }
                ),
            },
        }

        data_esperada = {
            "i_sc": [2.584939e-26, 0.0, 0.0],
            "v_oc": [0.0, 0.0, 0.0],
            "i_mp": [2.584939e-26, 0.0, 0.0],
            "v_mp": [0.0, 0.0, 0.0],
            "p_mp": [0.0, 0.0, 0.0],
            "i_x": [2.584939e-26, 0.0, 0.0],
            "i_xx": [2.584939e-26, 0.0, 0.0],
        }

        df_esperado = pd.DataFrame(
            data_esperada,
            index=pd.to_datetime(
                ["09:00", "12:00", "18:00"], format="%H:%M"
            ).tz_localize("America/Bogota"),
        )

        self.servicio_solar_instancia.ejecutar_calculo_solucion_cec()

        columnas_resultados = self.servicio_solar_instancia.inversores_resultados[
            "data"
        ]["solucion_cec"].columns

        columnas_esperadas = ["i_sc", "v_oc", "i_mp", "v_mp", "p_mp", "i_x", "i_xx"]

        # Asegurar que las columnas generadas son las columnas esperadas
        assert all([col in columnas_resultados for col in columnas_esperadas])

        # Asegurar que la estructura del Dataframe es la esperada
        pdt.assert_frame_equal(
            self.servicio_solar_instancia.inversores_resultados["data"]["solucion_cec"],
            df_esperado,
        )

    def test_ejecutar_calculo_energia(self):
        # Creando datos ficticios para 'inversores_resultados'
        index = pd.date_range(start="2008-01-01 00:00:00-05:00", periods=5, freq="H")
        energia_ac = pd.Series(1.191960e04 * 1000, index=index)  # Energía en Wh

        inversores = {
            "inversor_1": pd.DataFrame({"energia_ac": energia_ac}),
            "inversor_2": pd.DataFrame({"energia_ac": energia_ac}),
        }

        # Llamando al método
        resultado = self.servicio_solar_instancia.ejecutar_calculo_energia(
            inversores)

        # Datos esperados
        # Dado que hay dos inversores con la misma energía y se convierte a kWh
        resultado_esperado = 2 * energia_ac / 1000
        resultado_esperado.name = "energia_kWh"  # Asignamos el nombre a la serie

        # Asegurando que el resultado sea el esperado
        pd.testing.assert_series_equal(resultado, resultado_esperado)

    def parametros_transversales_enficc(self):
        return ParametrosTransversales(
            NombrePlanta="TestPlant",
            Cen=5,
            Ihf=0.2,
            Kpc=1,
            Kt=1,
            Kin=1,
            Latitud=45,
            Longitud=45,
            InformacionMedida=True,
            ZonaHoraria="UTC+5",
            Altitud=1000.0,
            Albedo=0.3,
            L=500.0,
            Ppi=11.0,
        )

    def test_calculo_enficc_normal(self):
        params = self.parametros_transversales_enficc()
        df = pd.DataFrame(
            {"diaria": [10, 20, 30, 40, 50]},
            index=pd.date_range("2023-01-01", periods=5),
        )
        result = self.servicio_solar_instancia.calcular_enficc(params, df)
        assert result.anio == 2023
        assert result.mes == 1
        assert result.valor == min(10, 12 * 5 * (1 - 0.2) * 1000)

    def test_calculo_enficc_informacion_no_medida(self):
        params = self.parametros_transversales_enficc()
        params.InformacionMedida = False
        df = pd.DataFrame(
            {"diaria": [10, 20, 30, 40, 50]},
            index=pd.date_range("2023-01-01", periods=5),
        )
        result = self.servicio_solar_instancia.calcular_enficc(params, df)
        assert result.anio == 2023
        assert result.mes == 1
        assert result.valor == int(10 * 0.6)

    def test_calculo_enficc_dataframe_vacio(self):
        params = self.parametros_transversales_enficc()
        df = pd.DataFrame()
        # Aquí esperamos que se genere una excepción porque el DataFrame está vacío
        with self.assertRaises(Exception):
            self.servicio_solar_instancia.calcular_enficc(params, df)

    # @mock.patch('dominio.servicio.azure_blob.cliente_azure.ClienteAzure')

    def test_generar_dataframe(self):
        nombre_blob = "blob"

        mock_cliente_azure = MockClienteAzure(nombre_blob)

        with mock.patch(
            "dominio.servicio.azure_blob.cliente_azure.ClienteAzure",
            return_value=mock_cliente_azure,
        ):
            # Llama a la función generar_dataframe
            df = self.servicio_solar_instancia.generar_dataframe(nombre_blob)

        mock_cliente_azure.archivo_leer.assert_called()

        # Verifica que df sea el valor esperado (puedes ajustar esto según tu caso)
        self.assertEqual(df, "Contenido simulado")

        # df = self.servicio_solar_instancia.generar_dataframe(nombre_blob)

        # self.assertEqual(df, mock_archivo_leer)
        mock_cliente_azure.assert_called_once_with(blob=nombre_blob)
        mock_cliente_azure.archivo_leer.assert_called_once()

    def test_ejecutar_calculo_dc_ac(self):
        self.servicio_solar_instancia.calculo_dc_ac = mock.Mock()


        self.servicio_solar_instancia.calculo_dc_ac.calculo_potencia_dc_ac.return_value = [
            10, 20, 30]
        mock_sys = mock.MagicMock()
        mock_params_trans = mock.MagicMock()
        mock_params_inv = mock.MagicMock()
        mock_params_mod = mock.MagicMock()

        self.servicio_solar_instancia.inversores_resultados = {
            "data_1": mock_data_1,
            "data_2": mock_data_2,
        }
        self.servicio_solar_instancia.inversores_pvsystem = {
            "pvsys_1": mock_pvsys_1,
            "pvsys_2": mock_pvsys_2,
        }

        self.servicio_solar_instancia.ejecutar_calculo_dc_ac(params_trans)

        self.assertEqual(
            self.servicio_solar_instancia.calculo_dc_ac.calculo_potencia_dc_ac.call_count,
            2,
        )

        self.servicio_solar_instancia.calculo_dc_ac.calculo_potencia_dc_ac.assert_any_call(
            mock_data_1, mock_pvsys_1, params_trans
        )

        self.servicio_solar_instancia.calculo_dc_ac.calculo_potencia_dc_ac.assert_any_call(
            mock_data_2, mock_pvsys_2, params_trans
        )

    """
    def test_calcular_eda(self):
        mock_params = ParametrosTransversales(
            NombrePlanta="TestPlant",
            Cen=2,
            Ihf=87,
            Ppi=11.0,
            Kpc=1,
            Kt=1,
            Kin=1,
            Latitud=45,
            Longitud=45,
            InformacionMedida=True,
            Elevacion=0.3,
            Voltaje=0.3,
            ZonaHoraria="",
            Altitud=15.3,
            Albedo=12.0,
            L=1.2

        )

        self.servicio_solar_instancia.calculo_dc_ac.calculo_potencia_dc_ac.assert_called_once_with(
            mock_sys, lista_array, mock_params_trans, mock_params_inv, mock_params_mod
        )

        assert resultado == [10, 20, 30]

        resultado_eda = self.servicio_solar_instancia.calcular_eda(
            mock_params, mock_energia_al_mes, resultado_enficc)

        self.assertEqual(len(resultado_eda), 12)
        for mes in resultado_eda:
            if mes.mes == 1:
                self.assertEqual(mes.valor, 0)
            elif mes.mes == 12:
                self.assertEqual(mes.valor, None)
            else:
                self.assertEqual(
                    mes.valor, (mock_energia_al_mes[mes.mes - 1] - resultado_enficc.valor).round(2))
    """


    def test_generar_lista_meses(self):
        anio = 2023
        lista_meses = self.servicio_solar_instancia.generar_lista_meses(anio)
        self.assertEqual(len(lista_meses), 12)
        for mes in lista_meses:
            self.assertIsInstance(mes, Resultado)

    def test_generar_archivo_excel(self):
        # Crear datos simulados para las entradas
        mock_energia_planta = mock.MagicMock()
        mock_energia_mes = mock.MagicMock()
        mock_energia_diaria = mock.MagicMock()
        mock_enficc = Resultado(anio=2023, mes=1, valor=100)
        mock_eda = [Resultado(anio=2023, mes=1, valor=0)]
        nombre_archivo = "nombre_de_prueba_resultado.xlsx"

        # Configurar mocks para las funciones transform_energia_planta, transform_energia_mes, transform_energia_diaria

        self.servicio_solar_instancia.manipulador_df.transform_energia_planta = (
            mock.MagicMock(return_value=mock_energia_planta)
        )
        self.servicio_solar_instancia.manipulador_df.transform_energia_mes = (
            mock.MagicMock(return_value=mock_energia_mes)
        )
        self.servicio_solar_instancia.manipulador_df.transform_energia_diaria = (
            mock.MagicMock(return_value=mock_energia_diaria)
        )
        self.servicio_solar_instancia.manipulador_df.transform_enficc = mock.MagicMock(
            return_value=mock_enficc
        )
        self.servicio_solar_instancia.manipulador_df.transform_eda = mock.MagicMock(
            return_value=mock_eda
        )

        # Configurar un mock para la función generar_archivo_excel_y_subir
        mock_cliente_azure = mock.MagicMock()
        self.servicio_solar_instancia.cliente_azure = mock_cliente_azure

        # Llamar a la función que se está probando
        self.servicio_solar_instancia.generar_archivo_excel(
            mock_energia_planta,
            mock_energia_mes,
            mock_energia_diaria,
            mock_enficc,
            mock_eda,
            nombre_archivo,
        )

        # Verificar que las funciones de transformación se llamaron con los datos correctos
        self.servicio_solar_instancia.manipulador_df.transform_energia_planta.assert_called_with(
            mock_energia_planta
        )
        self.servicio_solar_instancia.manipulador_df.transform_energia_mes.assert_called_with(
            mock_energia_mes
        )
        self.servicio_solar_instancia.manipulador_df.transform_energia_diaria.assert_called_with(
            mock_energia_diaria
        )
        self.servicio_solar_instancia.manipulador_df.transform_enficc.assert_called_with(
            mock_enficc
        )
        self.servicio_solar_instancia.manipulador_df.transform_eda.assert_called_with(
            mock_eda
        )

        # Verificar que la función generar_archivo_excel_y_subir se llamó con los datos y el nombre de archivo correctos
        diccionario_hojas = {
            "E_Horaria": mock_energia_planta,
            "E_Mensual": mock_energia_mes,
            "Em": mock_energia_diaria,
            "ENFICC": mock_enficc,
            "EDA": mock_eda,
        }
        self.servicio_solar_instancia.cliente_azure.generar_archivo_excel_y_subir.assert_called_with(
            diccionario_hojas, nombre_archivo
        )

    def test_servicio_solar_initialization(self):
        servicio = ServicioSolar()
        self.assertIsNotNone(servicio.manipulador_df)
        self.assertIsNotNone(servicio.calculo_dni_dhi)
        self.assertIsNotNone(servicio.calculo_dc_ac)
        self.assertIsNone(servicio.cliente_azure)
        self.assertIsNotNone(servicio.generar_archivo)
        self.assertIsNone(servicio.inversores_pvsystem)
        self.assertIsNone(servicio.inversores_resultados)

    @patch.object(ClienteAzure, "archivo_leer")
    @patch.object(ClienteAzure, "archivo_blob_borrar")
    @mock.patch("dominio.servicio.azure_blob.cliente_azure.ClienteAzure._ClienteAzure__instancia_cliente_azure_init")
    @mock.patch("dominio.servicio.azure_blob.cliente_azure.ClienteAzure._ClienteAzure__blob_storage_init")
    @mock.patch("dominio.servicio.azure_blob.cliente_azure.ClienteAzure._ClienteAzure__archivo_blob_obtener")    
    def test_generar_dataframe(self, mock_archivo_obtener, mock_storage_init, mock_azure_init, mock_archivo_borrar, mock_archivo_leer):
        # Suponiendo que ClienteAzure.archivo_leer() devuelve un DataFrame de Polars
        expected_df = pl.DataFrame({"column1": [1, 2, 3], "column2": ["a", "b", "c"]})

        # Configura el mock para devolver el DataFrame esperado
        mock_archivo_leer.return_value = expected_df
        servicio_solar = ServicioSolar()
        nombre_blob = "test_blob_name"
        result_df = servicio_solar.generar_dataframe(nombre_blob)

        mock_archivo_leer.assert_called_once()
        mock_archivo_borrar.assert_called_once()
        self.assertTrue(
            result_df.frame_equal(expected_df),
            "El DataFrame devuelto por generar_dataframe no coincide con el DataFrame esperado",
        )

    @patch("dominio.servicio.solar.servicio_solares.poa_bifacial")
    def test_calculo_poa_bifacial(self, mock_poa_bifacial):
        # Configura el mock para devolver un DataFrame de Pandas como resultado simulado
        mock_poa_bifacial.return_value = pd.DataFrame({"poa": [100, 200, 300]})

        df_dni_dhi = MagicMock()
        montura = MagicMock()
        params_trans = MagicMock()
        params_inv = MagicMock()
        params_array = MagicMock()

        # Configurar para simular un módulo bifacial
        params_inv.ParametrosModulo.Bifacial = True
        servicio_solar_instancia = ServicioSolar()

        # Ejecutar la función calculo_poa
        poa_resultado = servicio_solar_instancia.calculo_poa(
            df_dni_dhi, montura, params_trans, params_inv, params_array
        )

        # Verificar que la función poa_bifacial fue llamada
        mock_poa_bifacial.assert_called()

        self.assertIsInstance(poa_resultado, pd.DataFrame)
        # Verifica que los datos en el DataFrame son como se espera
        pd.testing.assert_frame_equal(
            poa_resultado, pd.DataFrame({"poa": [100, 200, 300]})

        )

    @patch("dominio.servicio.solar.servicio_solares.crear_montura_con_seguidores")
    @patch("dominio.servicio.solar.servicio_solares.crear_array")
    @patch("dominio.servicio.solar.servicio_solares.ServicioSolar.calculo_poa")
    def test_ejecutar_calculo_poa_con_seguidores(
        self, mock_calculo_poa, mock_crear_array, mock_crear_montura_con_seguidores
    ):
        """
        Testea la rama del if de ejecutar_calculo_poa cuando la estructura de planta tiene seguidores.
        """
        # Configura los mocks y parámetros
        mock_crear_montura_con_seguidores.return_value = MagicMock(
            name="MonturaConSeguidores"
        )
        mock_crear_array.return_value = MagicMock(name="Array")
        mock_calculo_poa.return_value = MagicMock(name="POA")

        mock_params = MagicMock(spec=JsonModelSolar)
        mock_params.ParametrosTransversales = MagicMock()
        mock_params.ParametrosConfiguracion = MagicMock()
        mock_params_inv = MagicMock()
        mock_params_array = MagicMock()
        mock_params_inv.EstructuraYConfiguracion = MagicMock(
            EstructuraPlantaConSeguidores=True
        )
        mock_params_inv.EstructuraYConfiguracion.CantidadPanelConectados = [
            mock_params_array
        ]

        mock_params.ParametrosConfiguracion.GrupoInversores = [mock_params_inv]

        # Crea un DataFrame simulado
        mock_df_dni_dhi = MagicMock()

        # Crea la instancia de ServicioSolar y llama al método
        servicio_solar = ServicioSolar()
        servicio_solar.ejecutar_calculo_poa(mock_df_dni_dhi, mock_params)

        # Verifica las llamadas y aserciones
        mock_crear_montura_con_seguidores.assert_called_once_with(
            mock_params_array)
        mock_crear_array.assert_called_once()
        mock_calculo_poa.assert_called_once()

    @patch("dominio.servicio.solar.servicio_solares.crear_montura_no_seguidores")
    @patch("dominio.servicio.solar.servicio_solares.crear_array")
    @patch("dominio.servicio.solar.servicio_solares.ServicioSolar.calculo_poa")
    def test_ejecutar_calculo_poa_sin_seguidores(
        self, mock_calculo_poa, mock_crear_array, mock_crear_montura_no_seguidores
    ):
        """
        Testea la rama del else de ejecutar_calculo_poa cuando la estructura de planta no tiene seguidores.
        """
        # Configura los mocks y parámetros
        mock_crear_montura_no_seguidores.return_value = MagicMock(
            name="MonturaNoSeguidores"
        )
        mock_crear_array.return_value = MagicMock(name="Array")
        mock_calculo_poa.return_value = MagicMock(name="POA")

        mock_params = MagicMock(spec=JsonModelSolar)
        mock_params.ParametrosTransversales = MagicMock()
        # mock parametros configuracion
        mock_params.ParametrosConfiguracion = MagicMock()

        mock_params_inv = MagicMock()
        mock_params_array = MagicMock()
        mock_params_inv.EstructuraYConfiguracion = MagicMock(
            EstructuraPlantaConSeguidores=False
        )
        mock_params_inv.EstructuraYConfiguracion.CantidadPanelConectados = [
            mock_params_array
        ]

        mock_params.ParametrosConfiguracion.GrupoInversores = [mock_params_inv]

        # Crea un DataFrame simulado
        mock_df_dni_dhi = MagicMock()

        # Crea la instancia de ServicioSolar y llama al método
        servicio_solar = ServicioSolar()
        servicio_solar.ejecutar_calculo_poa(mock_df_dni_dhi, mock_params)

        # Verifica las llamadas y aserciones
        mock_crear_montura_no_seguidores.assert_called_once_with(
            mock_params_array)
        mock_crear_array.assert_called_once()
        mock_calculo_poa.assert_called_once()

    """
    @patch('dominio.servicio.solar.servicio_solares.ClienteAzure')
    @patch('dominio.servicio.solar.servicio_solares.GenerarArchivoExcel')
    @patch('dominio.servicio.solar.servicio_solares.CalculoDCAC')
    @patch('dominio.servicio.solar.servicio_solares.CalculoDniDhi')
    @patch('dominio.servicio.solar.servicio_solares.ManipuladorDataframe')
    @patch('dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculo_poa')
    @patch('dominio.servicio.solar.servicio_solares.ManipuladorDataframe.filtrar_dataframe')
    def test_ejecutar_calculos(self,mock_filtrar_dataframe, mock_ejecutar_calculo_poa, mock_ManipuladorDataframe, 
                               mock_CalculoDniDhi, mock_CalculoDCAC, 
                               mock_GenerarArchivoExcel, mock_ClienteAzure):
        # Configure mocks
        mock_df = MagicMock(spec=pl.DataFrame)
        mock_df.to_pandas.return_value = pd.DataFrame({'Ghi': ['1,000', '2,000'], 'Ta': ['25,5', '30,2']})
        mock_params = MagicMock(spec=JsonModelSolar)
        mock_params.ParametrosTransversales = MagicMock()
        mock_params.ParametrosConfiguracion = MagicMock()


    #     # Set up the return value for the filtrar_dataframe method
    #     mock_filtrar_dataframe.return_value = MagicMock()

    #     # Set up the return value for the ejecutar_calculo_poa method
    #     mock_pvsystem = MagicMock()
    #     mock_resultados = MagicMock()
    #     mock_ejecutar_calculo_poa.return_value = (
    #         mock_pvsystem, mock_resultados)

        # Check that the result contains the expected data
        # This would require you to know the expected result or mock it
        # self.assertEqual(resultado.nombre_archivo, expected_file_name)
        # self.assertIsInstance(resultado.enficc, Resultado)
        # self.assertIsInstance(resultado.eda, list)
    """
    """


    #     # Assume ClienteAzure has been properly mocked and returns a blob name
    #     servicio_solar.cliente_azure = mock_ClienteAzure

    #     # Mock the calls and their return values within ejecutar_calculos
    #     mock_CalculoDniDhi.return_value = MagicMock(spec=pd.Series)
    #     mock_CalculoDCAC.return_value = MagicMock()
    #     mock_GenerarArchivoExcel.return_value = MagicMock()

    #     # Call the method
    #     resultado = servicio_solar.ejecutar_calculos(mock_df, mock_params)

    #     # Assertions to make sure each step was called
    #     mock_ManipuladorDataframe.filtrar_dataframe.assert_called_once()
    #     mock_ejecutar_calculo_poa.assert_called_once()
    #     mock_CalculoDniDhi.assert_called()
    #     mock_CalculoDCAC.assert_called()
    #     mock_GenerarArchivoExcel.assert_called()
    #     mock_filtrar_dataframe.assert_called_once()

    #     # You can add more specific assertions here

        # Assert that the expected calls are made
        mock_cliente_azure.generar_archivo_excel_y_subir.assert_called_once()
        # Additional assertions on the calls arguments, such as:
        called_args = mock_cliente_azure.generar_archivo_excel_y_subir.call_args[0][0]
        self.assertEqual(called_args.keys(), expected_excel_contents.keys())
        for sheet_name, data_frame in called_args.items():
            self.assertEqual(data_frame, expected_excel_contents[sheet_name])
    """

    @patch("dominio.servicio.solar.servicio_solares.CalculoDCAC")
    def test_ejecutar_calculo_dc_ac(self, mock_calculo_dc_ac_class):
        # Instancia de ServicioSolar
        servicio_solar = ServicioSolar()

        # Crear mocks para los parámetros de entrada
        pvsys = MagicMock(spec=PVSystem)
        lista_array = [MagicMock(), MagicMock()]  # Lista de mocks
        params_trans = MagicMock(spec=ParametrosTransversales)
        params_inversor = MagicMock(spec=ParametrosInversor)
        params_modulo = MagicMock(spec=ParametrosModulo)

        # Mock para el resultado esperado de calculo_potencia_dc_ac
        resultado_esperado = [123, 456]  # Ejemplo de resultado
        servicio_solar.calculo_dc_ac = MagicMock()
        servicio_solar.calculo_dc_ac.calculo_potencia_dc_ac.return_value = (
            resultado_esperado
        )

        # Llamada al método a probar
        resultado = servicio_solar.ejecutar_calculo_dc_ac(
            pvsys, lista_array, params_trans, params_inversor, params_modulo
        )

        # Verificar que el resultado es el esperado
        self.assertEqual(resultado, resultado_esperado)

        # Verificar que se hizo la llamada correcta al método mockeado
        servicio_solar.calculo_dc_ac.calculo_potencia_dc_ac.assert_called_once_with(
            pvsys, lista_array, params_trans, params_inversor, params_modulo
        )

    @patch("dominio.servicio.solar.servicio_solares.CalculoDCAC")
    def test_ejecutar_calculo_energia(self, mock_calculo_dc_ac_class):
        # Instancia de ServicioSolar
        servicio_solar = ServicioSolar()

        # Crear un diccionario simulado de inversores con DataFrames de Pandas como valores
        inversores_mock = {
            "inversor1": DataFrame({"data": [1, 2, 3]}),
            "inversor2": DataFrame({"data": [4, 5, 6]}),
        }

        # Mock para el resultado esperado de obtener_energia
        resultado_esperado = DataFrame({"energia": [10, 15, 20]})
        servicio_solar.calculo_dc_ac = MagicMock()
        servicio_solar.calculo_dc_ac.obtener_energia.return_value = resultado_esperado

        # Llamada al método a probar
        resultado = servicio_solar.ejecutar_calculo_energia(inversores_mock)

        # Verificar que el resultado es el esperado
        self.assertEqual(resultado.equals(resultado_esperado), True)

        # Verificar que se hizo la llamada correcta al método mockeado
        servicio_solar.calculo_dc_ac.obtener_energia.assert_called_once()

    # @patch(
    #     "dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculo_dni_dhi"
    # )
    # @patch("dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculo_poa")
    # @patch(
    #     "dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculo_dc_ac"
    # )
    # @patch(
    #     "dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculo_energia"
    # )
    # @patch("dominio.servicio.solar.servicio_solares.ServicioSolar.calcular_enficc")
    # @patch("utils.manipulador_dataframe.ManipuladorDataframe.calcular_eda")
    # @patch("dominio.servicio.solar.servicio_solares.GenerarArchivoExcel")
    # def test_ejecutar_calculos(
    #     self,
    #     mock_generar_archivo_excel,
    #     mock_calcular_eda,
    #     mock_calcular_enficc,
    #     mock_ejecutar_calculo_energia,
    #     mock_ejecutar_calculo_dc_ac,
    #     mock_ejecutar_calculo_poa,
    #     mock_ejecutar_calculo_dni_dhi,
    # ):
    #     servicio_solar = ServicioSolar()

    #     # Crear un DataFrame de Pandas con un DatetimeIndex
    #     indice_datetime = pd.date_range(start="2023-01-01", periods=2, freq="D")
    #     pandas_df = pd.DataFrame(
    #         {
    #             "Ghi": ["1,000", "2,000"],
    #             "Ta": ["25,5", "30,2"],
    #             "dni": [500, 600],
    #             "dhi": [100, 200],
    #         },
    #         index=indice_datetime,
    #     )

    #     # Crear un mock para un DataFrame de Polars
    #     mock_df = MagicMock(spec=pl.DataFrame)
    #     mock_df.to_pandas.return_value = pandas_df

    #     # Configurar mocks para ParametrosTransversales y JsonModelSolar
    #     mock_parametros_transversales = MagicMock(spec=ParametrosTransversales)
    #     mock_parametros_transversales.Ihf = 20  # Valor de ejemplo para Ihfmock_params_transversales.NombrePlanta = "PlantaSolar"
    #     mock_parametros_transversales.Cen = 1.0
    #     mock_parametros_transversales.Ihf = 0.1
    #     mock_parametros_transversales.Ppi = 1.0
    #     mock_parametros_transversales.Kpc = 1.0
    #     mock_parametros_transversales.Kt = 1.0
    #     mock_parametros_transversales.Kin = 1.0
    #     mock_parametros_transversales.Latitud = 1.0
    #     mock_parametros_transversales.Longitud = 1.0
    #     mock_parametros_transversales.InformacionMedida = True

    #     mock_params = MagicMock(spec=JsonModelSolar)
    #     mock_params.ParametrosTransversales = mock_parametros_transversales

    #     mock_ejecutar_calculo_dni_dhi.return_value = pandas_df.copy()
    #     mock_inversores_pvsystem = MagicMock()
    #     mock_inversores_resultados = MagicMock()
    #     # TODO se necesita enviar valores reales porque mock entra en recursion infinita
    #     #mock_ejecutar_calculo_poa.return_value = (mock_inversores_pvsystem, mock_inversores_resultados)


    #     # Llamada al método a probar
    #     respuesta = servicio_solar.ejecutar_calculos(mock_df, mock_params)

    #     # Verifica que el resultado sea del tipo esperado
    #     self.assertIsInstance(respuesta, Respuesta)

    #     # Verificar que se hicieron las llamadas correctas a los métodos mockeados
    #     mock_ejecutar_calculo_dni_dhi.assert_called_once()
    #     mock_ejecutar_calculo_poa.assert_called_once()
    #     mock_ejecutar_calculo_dc_ac.assert_called_once()
    #     mock_ejecutar_calculo_energia.assert_called_once()
    #     mock_calcular_enficc.assert_called_once()
    #     mock_calcular_eda.assert_called_once()
    #     mock_generar_archivo_excel.assert_called_once()


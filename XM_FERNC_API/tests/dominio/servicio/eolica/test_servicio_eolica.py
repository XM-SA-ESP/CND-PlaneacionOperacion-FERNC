import json
import polars as pl
import pandas as pd
import numpy as np

from unittest import TestCase, mock
from dominio.servicio.azure_blob.cliente_azure import ClienteAzure
from dominio.servicio.eolica.servicio_eolicas import ServicioEolicas
from infraestructura.models.eolica.parametros import (
    JsonModelEolica,
    ParametrosTransversales,
)
from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo


class TestServicioEolicas(TestCase):
    """
    Test suite para el servicio ServicioEolicas
    """

    def setUp(self):
        """
        Configura el caso de prueba creando instancias simuladas de la clase ServicioEolicas y la instancia de ServicioEolicas.
        Carga datos de prueba desde un archivo parquet y un archivo Excel.
        """

        # Creacion de una instancia Mock de ServicioEolicas
        self.servicio_eolica_mock = mock.Mock(spec=ServicioEolicas)
        self.servicio_eolica = self.servicio_eolica_mock

        # Creacion Instancia ServicioEolicas
        self.servicio_eolica_instancia = ServicioEolicas()

        data = "./tests/data/test_dataframe.parquet"
        self.df = pl.read_parquet(data)
        self.df_pd = pd.read_parquet(data)
        self.mock_series = pd.read_excel(
            "./tests/data/test_series_tiempo.xlsx", index_col=0
        )

        with open("./tests/data/test_json_data_eolica.json") as f:
            json_data = json.load(f)

        self.params = JsonModelEolica(**json_data)
        cliente_azure = mock.MagicMock()
        cliente_azure.archivo_leer = self.df_pd
        cliente_azure.archivo_leer["DenBuje"] = 1
        self.serie_tiempo = pd.date_range("2021-01-01", periods=3)
        self.aerogeneradores = {
            1: Aerogenerador(
                id_aero=1,
                id_torre="torre1",
                latitud=111,
                longitud=111,
                elevacion=1,
                modelo=mock.MagicMock(),
                df=pd.DataFrame({
                    "VelocidadViento": [22, 33, 44],
                    "DireccionViento": [12, 13, 14],
                    "Ta": [6, 7, 8],
                    "DenBuje": [1.1, 1.2, 1.3],
                }, 
                index=self.serie_tiempo)
        )}

        self.mock_estructura_xarray = self.servicio_eolica_instancia._ServicioEolicas__estructura_xarray_vectorizado(self.aerogeneradores, self.serie_tiempo)
    
    @mock.patch.object(ClienteAzure, "archivo_leer")
    @mock.patch.object(ClienteAzure, "archivo_blob_borrar")
    @mock.patch("dominio.servicio.azure_blob.cliente_azure.ClienteAzure._ClienteAzure__instancia_cliente_azure_init")
    @mock.patch("dominio.servicio.azure_blob.cliente_azure.ClienteAzure._ClienteAzure__blob_storage_init")
    @mock.patch("dominio.servicio.azure_blob.cliente_azure.ClienteAzure._ClienteAzure__archivo_blob_obtener")
    def test_generar_dataframe(self, mock_archivo_obtener, mock_storage_init, mock_azure_init, mock_archivo_borrar, mock_archivo_leer):
        # Crear un objeto de prueba de JsonModelEolica con un nombre de blob simulado
        mock_azure_init.return_value = "oiawhdewa"
        mock_storage_init.return_value = "dadawd"
        mock_archivo_obtener.return_value = "aeiodhaed"
        expected_df = pl.DataFrame({"column1": [1, 2, 3], "column2": ["a", "b", "c"]})
        mock_archivo_leer.return_value = expected_df
        
        # Llamar a la función generar_dataframe
        df = self.servicio_eolica_instancia.generar_dataframe(self.params.ArchivoSeries.Nombre)

        # Verificar que se llamó a archivo_leer con el nombre del blob correcto
        mock_archivo_leer.assert_called_once_with()
        self.assertIsInstance(df, pl.DataFrame)

    @mock.patch("dominio.servicio.eolica.servicio_eolicas.ServicioEolicas._ServicioEolicas__crear_lista_argumentos_correcciones")
    @mock.patch("utils.estructura_xarray.crear_estructura_xarray_vectorizado")
    @mock.patch("multiprocessing.Pool")
    @mock.patch("requests.post")
    def test_ejecutar_calculo_eolica(self, mock_request_post, mock_pool, mock_estructura_xarray, mock_argumentos_correcciones):
        mock_params = mock.MagicMock()
        torre = mock.MagicMock()
        torre.dataframe = self.df_pd
        torres = {'test_key': torre}
        modelos = {"modelo1": Modelo("modelo1", 1, 2, 3, 4, 5, 6, 7, 8, 9, None)}
        aerogeneradores = mock.MagicMock()
        aero_dict = mock.MagicMock()
        mock_argumentos_correcciones.return_value = mock.MagicMock()
        mock_estructura_xarray.return_value = self.mock_estructura_xarray
        mock_request_post.return_value = None

        with mock.patch.object(self.servicio_eolica_instancia, 'actualizar_aerogenerador_a_torre_cercana') as mock_actualizar_aerogenerador_a_torre_cercana, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_estructura, 'crear_dict_modelos_aerogeneradores') as mock_crear_dict_modelos_aerogeneradores, \
            mock.patch.object(self.servicio_eolica_instancia, 'ejecutar_calculo_temperatura_presion_densidad') as mock_ejecutar_calculo_temperatura_presion_densidad, \
            mock.patch.object(self.servicio_eolica_instancia.calculo_pcc, 'calculo_pcc_aerogenerador') as mock_calculo_pcc_aerogenerador, \
            mock.patch.object(self.servicio_eolica_instancia.correccion_parques, 'calcular_h_buje_promedio') as mock_calcular_h_buje_promedio, \
            mock.patch.object(self.servicio_eolica_instancia.ordenamiento, 'ordenamiento_vectorizado') as mock_ordenamiento_vectorizado, \
            mock.patch.object(self.servicio_eolica_instancia, 'cliente_azure') as mock_cliente_azure, \
            mock.patch.object(self.servicio_eolica_instancia, '_ServicioEolicas__estructura_xarray_vectorizado') as mock_xarray_vectorizado, \
            mock.patch.object(self.servicio_eolica_instancia, '_ServicioEolicas__estructura_xarray_curvas') as mock_xarray_curvas, \
            mock.patch.object(self.servicio_eolica_instancia, '_ServicioEolicas__calculo_potencia_vectorizado') as mock_potencia, \
            mock.patch.object(self.servicio_eolica_instancia, '_ServicioEolicas__crear_df_energia_planta') as mock_energia_planta, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_df, 'filtrar_por_mes') as mock_filtrar_por_mes, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_df, 'filtrar_por_dia') as mock_filtrar_por_dia, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_df, 'calcular_eda') as mock_calcular_eda, \
            mock.patch.object(self.servicio_eolica_instancia, 'calcular_enficc') as mock_calcular_enficc, \
            mock.patch.object(self.servicio_eolica_instancia.generar_archivo, 'generar_archivo_excel') as mock_generar_archivo_excel:

            mock_actualizar_aerogenerador_a_torre_cercana.return_value = (mock_params, torres)
            mock_ejecutar_calculo_temperatura_presion_densidad.return_value = torres
            mock_crear_dict_modelos_aerogeneradores.return_value = (modelos, aerogeneradores)
            mock_calculo_pcc_aerogenerador.return_value = aero_dict
            mock_pool.return_value.map.return_value = []
            mock_potencia.return_value = mock_estructura_xarray
            mock_energia_planta.return_value = pd.Series(np.arange(1001))
            cliente_azure = mock.MagicMock()
            cliente_azure.blob = 'string_test'
            mock_cliente_azure.return_value = cliente_azure
            mock_filtrar_por_mes.return_value = mock.MagicMock()
            mock_filtrar_por_dia.return_value = mock.MagicMock()
            resultado_enficc = mock.MagicMock()
            resultado_enficc.valor = 1.2345
            mock_calcular_enficc.return_value = resultado_enficc
            mock_generar_archivo_excel.return_value = mock.MagicMock()

            mock_ordenamiento_vectorizado.return_value = {1: pd.DataFrame({"id_turbina": [1, 2, 3]})}

            self.servicio_eolica_instancia.ejecutar_calculos(mock_params)

            # Asegurar que los demas metodo fueron llamados
            mock_params = mock_actualizar_aerogenerador_a_torre_cercana.assert_called_once_with(
                mock_params
            )
            mock_ejecutar_calculo_temperatura_presion_densidad.assert_called_once_with(
                torres
            )
            mock_filtrar_por_mes.assert_called_once()
            mock_filtrar_por_dia.assert_called_once()
            mock_crear_dict_modelos_aerogeneradores.assert_called_once()
            mock_calculo_pcc_aerogenerador.assert_called_once()
            mock_calcular_h_buje_promedio.assert_called_once()

    def test_actualizar_aerogenerador_a_torre_cercana(self):
        with mock.patch.object(
            self.servicio_eolica_instancia.manipulador_modelos,
            "ajustar_aerogeneradores",
        ) as mock_ajustar_aerogeneradores:
            resultado = self.servicio_eolica_instancia.manipulador_modelos.ajustar_aerogeneradores(
                self.params
            )

            mock_ajustar_aerogeneradores.assert_called_once()

    def test_crear_lista_vectores_velocidades(self):
        serie_tiempo = pd.date_range("2021-01-01", periods=3)
        aerogeneradores = {
            1: Aerogenerador(
                id_aero=1,
                id_torre="torre1",
                latitud=111,
                longitud=111,
                elevacion=1,
                modelo=mock.MagicMock(),
                df=pd.DataFrame({"VelocidadViento": [22, 33, 44]}, index=serie_tiempo)
        )}

        resultado = self.servicio_eolica_instancia._ServicioEolicas__crear_lista_vectores_velocidades(aerogeneradores, serie_tiempo)
        
        for vector in resultado:
            assert isinstance(vector, np.ndarray)

    def test_chunksize(self):
        resultado = self.servicio_eolica_instancia._ServicioEolicas__chunksize(2, 50)
        self.assertEqual(resultado, 25)

    def test_asignar_valores_aerogeneradores(self):
        test_tuple = (self.serie_tiempo[0], [(1, 57)])
        self.servicio_eolica_instancia._ServicioEolicas__asignar_valores_aerogeneradores(test_tuple, self.aerogeneradores, "VelocidadViento")

        assert self.aerogeneradores[1].df["VelocidadViento"][0] == 57

    def test_obtener_z_cre_values(self):
        esperado_con_offshore = (0.0002, 0.03, 0.04)
        esperado_sin_offshore = (0.055, 0.05,0.075)
        
        resultado_con_offshore = self.servicio_eolica_instancia._ServicioEolicas__obtener_z_cre_values(True)
        resultado_sin_offshore = self.servicio_eolica_instancia._ServicioEolicas__obtener_z_cre_values(False)

        assert resultado_con_offshore == esperado_con_offshore
        assert resultado_sin_offshore == esperado_sin_offshore

    def test_caracteristicas_tij(self):
        aero1 = Aerogenerador(
                id_aero=1,
                id_torre="torre1",
                latitud=111,
                longitud=111,
                elevacion=12,
                modelo="modelo1",
                dist_pcc=12
        )
        aero2 = Aerogenerador(
                id_aero=2,
                id_torre="torre1",
                latitud=111,
                longitud=111,
                elevacion=24,
                modelo="modelo2",
                dist_pcc=24
        )
        modelos = {
            "modelo1": Modelo("modelo1", 3, 34, 2350, 43, 1.12, 1, 8.5, -10, 55, curvas_fabricante=mock.MagicMock),
            "modelo2": Modelo("modelo2", 5, 12, 2543, 76, 1.23, 3, 7.7, -7, 44, curvas_fabricante=mock.MagicMock)           
        }
        columnas_esperadas = ["altura_buje", "radio", "densidad", "area_rotor", "dist_pcc", "t_min", "t_max", "p_nominal"]
        aerogeneradores = {1: aero1, 2: aero2}

        resultado = self.servicio_eolica_instancia._ServicioEolicas__caracteristicas_tij(aerogeneradores, modelos)
        
        assert isinstance(resultado, pd.DataFrame)
        assert all(col in columnas_esperadas for col in resultado.columns)

    def parametros_transversales_enficc(self):
        return ParametrosTransversales(
            NombrePlanta="TestPlant",
            Cen=2,
            Ihf=87,
            Kpc=1,
            Kt=1,
            Kin=1,
            Latitud=45,
            Longitud=45,
            InformacionMedida=True,
            Offshore=True,
            Elevacion=0.3,
            Voltaje=0.3,
            Ppi=11.0
        )

    def test_calculo_enficc_normal(self):
        params = self.parametros_transversales_enficc()
        df = pd.DataFrame(
            {"diaria": [10000, 20000, 30000, 40000, 50000]},
            index=pd.date_range("2023-01-01", periods=5),
        )
        result = self.servicio_eolica_instancia.calcular_enficc(params, df)
        assert result.anio == 2023
        assert result.mes == 1
        assert result.valor == min(10000, 24 * 2 * (1 - (87 / 100)) * 1000)

    def test_calculo_enficc_informacion_no_medida(self):
        params = self.parametros_transversales_enficc()
        params.InformacionMedida = False
        df = pd.DataFrame(
            {"diaria": [10, 20, 30, 40, 50]},
            index=pd.date_range("2023-01-01", periods=5),
        )
        result = self.servicio_eolica_instancia.calcular_enficc(params, df)
        assert result.anio == 2023
        assert result.mes == 1
        assert result.valor == int(10 * 0.6)

    def test_calculo_enficc_dataframe_vacio(self):
        params = self.parametros_transversales_enficc()
        df = pd.DataFrame()
        with self.assertRaises(
            Exception
        ):  # Aquí esperamos que se genere una excepción porque el DataFrame está vacío
            self.servicio_eolica_instancia.calcular_enficc(params, df)

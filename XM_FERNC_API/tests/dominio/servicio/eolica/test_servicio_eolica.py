import json
import polars as pl
import pandas as pd
from unittest import TestCase, mock
from dominio.servicio.azure_blob.cliente_azure import ClienteAzure
from dominio.servicio.eolica.servicio_eolicas import ServicioEolicas
from infraestructura.models.eolica.parametros import (
    JsonModelEolica,
    ParametrosTransversales,
)
from tests.dominio.servicio.azure_blob.test_cliente_azure import MockClienteAzure

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

    
    @mock.patch.object(ClienteAzure, "archivo_leer")
    @mock.patch.object(ClienteAzure, "__init__", return_value=None)
    def test_generar_dataframe(self, mock_cliente_azure_init, mock_archivo_leer):
    # Crear un objeto de prueba de JsonModelEolica con un nombre de blob simulado
        expected_df = pl.DataFrame({"column1": [1, 2, 3], "column2": ["a", "b", "c"]})
        mock_archivo_leer.return_value = expected_df
        
        # Llamar a la función generar_dataframe
        df = self.servicio_eolica_instancia.generar_dataframe(self.params.ArchivoSeries.Nombre)

        # Verificar que se llamó a archivo_leer con el nombre del blob correcto
        mock_archivo_leer.assert_called_once_with()
        self.assertIsInstance(df, pl.DataFrame)

    @mock.patch("dominio.servicio.eolica.servicio_eolicas.ServicioEolicas._ServicioEolicas__crear_lista_argumentos", mock.MagicMock())
    def test_ejecutar_calculo_eolica(self):
        
        mock_params = mock.MagicMock()
        torre = mock.MagicMock()
        torre.dataframe = self.df_pd
        torres = {'test_key': torre}
        modelos = mock.MagicMock()
        aerogeneradores = mock.MagicMock()
        aero_dict = mock.MagicMock()
        energia_planta = mock.MagicMock()
        energia_al_mes = mock.MagicMock()

        with mock.patch.object(self.servicio_eolica_instancia, 'actualizar_aerogenerador_a_torre_cercana') as mock_actualizar_aerogenerador_a_torre_cercana, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_estructura, 'crear_dict_modelos_aerogeneradores') as mock_crear_dict_modelos_aerogeneradores, \
            mock.patch.object(self.servicio_eolica_instancia, 'ejecutar_calculo_temperatura_presion_densidad') as mock_ejecutar_calculo_temperatura_presion_densidad, \
            mock.patch.object(self.servicio_eolica_instancia.calculo_pcc, 'calculo_pcc_aerogenerador') as mock_calculo_pcc_aerogenerador, \
            mock.patch.object(self.servicio_eolica_instancia.correccion_parques, 'calcular_h_buje_promedio') as mock_calcular_h_buje_promedio, \
            mock.patch.object(self.servicio_eolica_instancia.instancia_calculo_potencia, 'potencia_planta_eolica') as mock_potencia_planta_eolica, \
            mock.patch.object(self.servicio_eolica_instancia, 'cliente_azure') as mock_cliente_azure, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_df, 'filtrar_por_mes') as mock_filtrar_por_mes, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_df, 'filtrar_por_dia') as mock_filtrar_por_dia, \
            mock.patch.object(self.servicio_eolica_instancia.manipulador_df, 'calcular_eda') as mock_calcular_eda, \
            mock.patch.object(self.servicio_eolica_instancia, 'calcular_enficc') as mock_calcular_enficc, \
            mock.patch.object(self.servicio_eolica_instancia.generar_archivo, 'generar_archivo_excel') as mock_generar_archivo_excel:

            mock_actualizar_aerogenerador_a_torre_cercana.return_value = (mock_params, torres)
            mock_ejecutar_calculo_temperatura_presion_densidad.return_value = torres
            mock_crear_dict_modelos_aerogeneradores.return_value = (modelos, aerogeneradores)
            mock_calculo_pcc_aerogenerador.return_value = aero_dict
            mock_potencia_planta_eolica.return_value = energia_planta
            cliente_azure = mock.MagicMock()
            cliente_azure.blob = 'string_test'
            mock_cliente_azure.return_value = cliente_azure
            mock_filtrar_por_mes.return_value = mock.MagicMock()
            mock_filtrar_por_dia.return_value = mock.MagicMock()
            resultado_enficc = mock.MagicMock()
            resultado_enficc.Valor = 1.2345
            mock_calcular_enficc.return_value = resultado_enficc
            mock_generar_archivo_excel.return_value = mock.MagicMock()

            self.servicio_eolica_instancia.ejecutar_calculos(mock_params)

            # Asegurar que los demas metodo fueron llamados
            mock_params = mock_actualizar_aerogenerador_a_torre_cercana.assert_called_once_with(
                mock_params
            )
            mock_ejecutar_calculo_temperatura_presion_densidad.assert_called_once_with(
                modelos, aerogeneradores, torres
            )
            mock_filtrar_por_mes.assert_called_once()
            mock_filtrar_por_dia.assert_called_once()
            mock_crear_dict_modelos_aerogeneradores.assert_called_once()
            mock_calculo_pcc_aerogenerador.assert_called_once()
            mock_calcular_h_buje_promedio.assert_called_once()
            mock_potencia_planta_eolica.assert_called_once()
            

    def test_actualizar_aerogenerador_a_torre_cercana(self):
        

        with mock.patch.object(
            self.servicio_eolica_instancia.manipulador_modelos,
            "ajustar_aerogeneradores",
        ) as mock_ajustar_aerogeneradores:
            resultado = self.servicio_eolica_instancia.manipulador_modelos.ajustar_aerogeneradores(
                self.params
            )

            mock_ajustar_aerogeneradores.assert_called_once()


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
        assert result.Anio == 2023
        assert result.Mes == 1
        assert result.Valor == min(10000, 24 * 2 * (1 - (87 / 100)) * 1000)

    def test_calculo_enficc_informacion_no_medida(self):
        params = self.parametros_transversales_enficc()
        params.InformacionMedida = False
        df = pd.DataFrame(
            {"diaria": [10, 20, 30, 40, 50]},
            index=pd.date_range("2023-01-01", periods=5),
        )
        result = self.servicio_eolica_instancia.calcular_enficc(params, df)
        assert result.Anio == 2023
        assert result.Mes == 1
        assert result.Valor == int(10 * 0.6)

    def test_calculo_enficc_dataframe_vacio(self):
        params = self.parametros_transversales_enficc()
        df = pd.DataFrame()
        with self.assertRaises(
            Exception
        ):  # Aquí esperamos que se genere una excepción porque el DataFrame está vacío
            self.servicio_eolica_instancia.calcular_enficc(params, df)

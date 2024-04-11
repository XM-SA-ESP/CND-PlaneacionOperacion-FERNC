import unittest
from unittest.mock import MagicMock, patch
from utils.generar_archivo_excel import GenerarArchivoExcel
from infraestructura.models.respuesta import Resultado

class TestGenerarArchivoExcel(unittest.TestCase):

    @patch("utils.manipulador_dataframe.ManipuladorDataframe")
    @patch("dominio.servicio.azure_blob.cliente_azure.ClienteAzure")
    def test_generar_archivo_excel(self, mock_cliente_azure, mock_manipulador_df):
        mock_manipulador_df_instance = MagicMock()
        mock_manipulador_df.return_value = mock_manipulador_df_instance

        generar_archivo_excel = GenerarArchivoExcel(mock_manipulador_df_instance)

        cliente_azure_mock = mock_cliente_azure.return_value
        energia_planta_mock = MagicMock()
        energia_mes_mock = MagicMock()
        energia_diaria_mock = MagicMock()
        enficc_mock = MagicMock()
        eda_mock = MagicMock()
        nombre_archivo_mock = "test_archivo.xlsx"

        generar_archivo_excel.generar_archivo_excel(
            cliente_azure_mock,
            energia_planta_mock,
            energia_mes_mock,
            energia_diaria_mock,
            enficc_mock,
            eda_mock,
            nombre_archivo_mock
        )

        mock_manipulador_df_instance.transform_energia_planta.assert_called_once_with(energia_planta_mock)
        mock_manipulador_df_instance.transform_energia_mes.assert_called_once_with(energia_mes_mock)
        mock_manipulador_df_instance.transform_energia_diaria.assert_called_once_with(energia_diaria_mock)
        mock_manipulador_df_instance.transform_enficc.assert_called_once_with(enficc_mock)
        mock_manipulador_df_instance.transform_eda.assert_called_once_with(eda_mock)

        diccionario_esperado = {
            "E_Horaria": mock_manipulador_df_instance.transform_energia_planta.return_value,
            "E_Mensual": mock_manipulador_df_instance.transform_energia_mes.return_value,
            "Em": mock_manipulador_df_instance.transform_energia_diaria.return_value,
            "ENFICC": mock_manipulador_df_instance.transform_enficc.return_value,
            "EDA": mock_manipulador_df_instance.transform_eda.return_value,
        }
        cliente_azure_mock.generar_archivo_excel_y_subir.assert_called_once_with(
            diccionario_esperado, nombre_archivo_mock
        )
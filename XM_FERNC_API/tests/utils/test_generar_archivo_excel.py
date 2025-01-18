import unittest
from unittest.mock import MagicMock, patch
from utils.generar_archivo_excel import GenerarArchivoExcel
from infraestructura.models.respuesta import Resultado
import os

class TestGenerarArchivoExcel(unittest.TestCase):
    @patch("utils.generar_archivo_excel.generar_archivo_excel_y_subir_volumen")  # Mock de la función externa
    def test_generar_archivo_excel(self, mock_generar_archivo_excel_y_subir):
        # Crear un mock del manipulador_df
        manipulador_mock = MagicMock()
        manipulador_mock.transform_energia_planta.return_value = "energia_planta_transformada"
        manipulador_mock.transform_energia_mes.return_value = "energia_mes_transformada"
        manipulador_mock.transform_energia_diaria.return_value = "energia_diaria_transformada"
        manipulador_mock.transform_enficc.return_value = "df_enficc_transformado"
        manipulador_mock.transform_eda.return_value = "df_eda_transformado"

        # Instanciar la clase con el mock
        generar_excel = GenerarArchivoExcel(manipulador_df=manipulador_mock)

        # Datos de entrada
        energia_planta = "energia_planta"
        energia_mes = "energia_mes"
        energia_diaria = "energia_diaria"
        enficc = "enficc"
        eda = "eda"
        nombre_archivo = "archivo_prueba.xlsx"

        # Llamar al método
        generar_excel.generar_archivo_excel(
            energia_planta, energia_mes, energia_diaria, enficc, eda, nombre_archivo
        )

        # Validar que los métodos de manipulador_df fueron llamados con los argumentos correctos
        manipulador_mock.transform_energia_planta.assert_called_once_with("energia_planta")
        manipulador_mock.transform_energia_mes.assert_called_once_with("energia_mes")
        manipulador_mock.transform_energia_diaria.assert_called_once_with("energia_diaria")
        manipulador_mock.transform_enficc.assert_called_once_with("enficc")
        manipulador_mock.transform_eda.assert_called_once_with("eda")

        # Validar que generar_archivo_excel_y_subir_volumen fue llamado con el diccionario esperado
        expected_diccionario_hojas = {
            "E_Horaria": "energia_planta_transformada",
            "E_Mensual": "energia_mes_transformada",
            "Em": "energia_diaria_transformada",
            "ENFICC": "df_enficc_transformado",
            "EDA": "df_eda_transformado",
        }
        mock_generar_archivo_excel_y_subir.assert_called_once_with(
            expected_diccionario_hojas, nombre_archivo
        )
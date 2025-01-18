import unittest
import polars as pl
import pandas as pd

from io import BytesIO
from unittest import mock
from unittest.mock import patch
from dominio.servicio.azure_blob.cliente_azure import ClienteAzure
from azure.storage.blob import BlobServiceClient
from azure.storage.blob._blob_client import BlobClient
from pandas.core.frame import DataFrame as Pandas_Dataframe


class MockClienteAzure(ClienteAzure):
    """Clase que simula el cliente de Azure Storage para Blob."""

    def __init__(self, blob):
        """Inicializa una instancia de MockClienteAzure.

        Args:
            blob: El nombre del blob.
        """
        self.cliente_blob_mock = mock.Mock(spec=BlobClient)
        self.cliente_storage_mock = mock.Mock(spec=BlobServiceClient)
        self.blob = blob
        self.container = mock.Mock(spec="container")
        self.instancia_servicio_cliente = self.cliente_storage_mock(
            self.cliente_blob_mock(b"mock data")
        )
        self.cliente_storage = self.__blob_storage_init()
        self.archivo_blob = self.__archivo_blob_obtener()

    def __blob_storage_init(self):
        """Inicializa el cliente de almacenamiento de blobs.

        Returns:
            El cliente de almacenamiento de blobs simulado.
        """
        return self.instancia_servicio_cliente.blob_client

    def __archivo_blob_obtener(self):
        """Obtiene el archivo de blob.

        Returns:
            El archivo de blob simulado.
        """
        # Devuelve un archivo Parquet válido
        df = pl.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
        parquet_file = BytesIO()
        df.write_parquet(parquet_file)
        parquet_file.seek(0)
        return parquet_file


class TestClienteAzure(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MockClienteAzure("blob")

    def test_archivo_leer(self):
        """Prueba la funcionalidad de lectura del archivo."""

        df = self.mock_client.archivo_leer()
        self.mock_client.cliente_blob_mock.assert_called()
        self.mock_client.cliente_storage_mock.assert_called()
        #assert isinstance(df, pl.DataFrame)
        assert len(df) == 3
        assert set(df.columns) == {"col1", "col2"}
        assert df["col1"].sum() == 6

    def test_archivo_subir(self):
        """Prueba la funcionalidad de subida del archivo."""
        with patch.object(
            self.mock_client.instancia_servicio_cliente, "get_blob_client"
        ) as mock_get_client:
            df = Pandas_Dataframe({"col1": [1, 2, 3], "col2": [4, 5, 6]})
            self.mock_client.archivo_subir(df, "nombre_blob")
            self.mock_client.cliente_storage_mock.assert_called()
            mock_get_client.assert_called_once()

    def test_archivo_blob_borrar(self):
        """Prueba la funcionalidad de borrado del archivo."""

        self.mock_client.archivo_blob_borrar()
        self.mock_client.cliente_storage_mock.assert_called()

    def test_archivo_blob_obtener(self):
        with patch.object(
            self.mock_client.cliente_storage, "download_blob"
        ) as mock_download:
            mock_download.return_value = BytesIO()
            self.mock_client._ClienteAzure__archivo_blob_obtener()
            mock_download.assert_called()

    @patch("dominio.servicio.azure_blob.cliente_azure.ExcelWriter")
    @patch("dominio.servicio.azure_blob.cliente_azure.BlobServiceClient")
    def test_generar_archivo_excel_y_subir(
        self, mock_blob_service_client, mock_excel_writer
    ):
        """Prueba la funcionalidad de generación y subida de archivo Excel."""
        # Create a mock blob client
        mock_blob_client = mock.MagicMock()
        mock_blob_service_client.return_value.get_blob_client.return_value = (
            mock_blob_client
        )
        # Create a mock Excel buffer
        mock_excel_buffer = BytesIO()
        mock_excel_writer.return_value.__enter__.return_value = mock_excel_buffer

        # Set up the test data
        diccionario_hojas = {
            "Hoja1": pd.DataFrame({"col1": [1, 2, 3]}),
            "Hoja2": pd.DataFrame({"col2": [4, 5, 6]}),
        }
        nombre_archivo = "test.xlsx"

        # Create an instance of the ClienteAzure class
        cliente_azure = MockClienteAzure("blob")

        # Call the method under test
        cliente_azure.generar_archivo_excel_y_subir(diccionario_hojas, nombre_archivo)

        # Verify that ExcelWriter and BlobServiceClient were called correctly
        mock_excel_writer.assert_called_with(mock.ANY, engine="xlsxwriter")

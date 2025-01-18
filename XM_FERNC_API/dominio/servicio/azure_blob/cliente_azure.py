import pandas as pd
import os
from typing import List
import pyarrow.parquet as pq

from io import BytesIO
from polars import exceptions
from pandas import ExcelWriter, Series
from azure.storage.blob import BlobServiceClient
from azure.storage.blob._blob_client import BlobClient
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from pyspark.sql import SparkSession, DataFrame



def generar_archivo_excel_y_subir_volumen( diccionario_hojas, nombre_archivo):
    """
    Esta función toma un diccionario de DataFrames o Series y un nombre de archivo,
    y escribe cada DataFrame o Serie en una hoja separada de un archivo Excel.
    Luego sube el archivo a Azure Blob Storage.

    Parámetros:
        diccionario_hojas (dict): Un diccionario donde cada clave es el nombre de la hoja,
                                y cada valor es un DataFrame o Serie.
        nombre_archivo (str): El nombre del archivo Excel que se creará.
        cliente_azure (ClienteAzure): Una instancia de la clase ClienteAzure.

    Retorna:
        None
    """
    # Crear un buffer en memoria para el archivo Excel
    excel_buffer = BytesIO()

    # Escribir DataFrames o Series en el buffer
    with ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        for nombre_hoja, datos in diccionario_hojas.items():
            if isinstance(datos, Series):
                # Si los datos son una Serie, conviértelos en un DataFrame
                datos = datos.to_frame()
            datos.to_excel(writer, sheet_name=nombre_hoja, index=False)

    # Rebobinar el buffer al inicio
    excel_buffer.seek(0)
    ruta_archivo = os.path.join(os.environ['VOLUME'], nombre_archivo)        
        
    if os.path.exists(ruta_archivo):
        spark = SparkSession.builder.getOrCreate()
        if 'PYTEST_CURRENT_TEST' not in os.environ:
            from pyspark.dbutils import DBUtils
            dbutils = DBUtils(spark)
            dbutils.fs.rm(ruta_archivo)

    with open(ruta_archivo, "wb") as f:
        f.write(excel_buffer.getvalue())

    return None



from pyspark.sql import DataFrame

class ClienteAzure:
    def __init__(
        self,
        blob: str
    ) -> None:
        self.blob = blob
        self.instancia_servicio_cliente = self.__instancia_cliente_azure_init()
        self.cliente_storage = self.__blob_storage_init()
        self.archivo_blob = self.__archivo_blob_obtener()        

    def __instancia_cliente_azure_init(self) -> BlobServiceClient:
        """
        Inicializa y devuelve una instancia de BlobServiceClient para conectarse al almacenamiento de blobs de Azure.

        Retorna:
            BlobServiceClient: La instancia inicializada de BlobServiceClient.
        """

        envimonment = os.environ.get("ENVIRONMENT")
        self.container = os.environ.get("CONTAINER")

        if envimonment == "dev":
            connection_string = os.environ.get("CONNECTION_STRING")
            return BlobServiceClient.from_connection_string(connection_string)

        keyvault_uri = os.environ.get("KEYVAULT_URI")
        keyvault_storage_account = os.environ.get("KEYVAULT_STORAGE_ACOUNT")

        credential = ClientSecretCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID"),
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET"),
        )

        secret_client = SecretClient(vault_url=keyvault_uri, credential=credential)
        storage_account_url = secret_client.get_secret(keyvault_storage_account)

        return BlobServiceClient(
            account_url=storage_account_url.value, credential=credential
        )

    def __blob_storage_init(self) -> BlobClient:
        """
        Inicializa el cliente de almacenamiento de blob.

        Retorna:
            BlobClient: El cliente de almacenamiento de blob.
            None: Si no se puede inicializar el cliente de blob.
        """

        try:
            cliente_storage = self.instancia_servicio_cliente.get_blob_client(
                container=self.container, blob=self.blob, snapshot=None
            )

            return cliente_storage
        except Exception as e:
            print(f"Error: {str(e)}")

    def __archivo_blob_obtener(self) -> BytesIO:
        """
        Recupera el archivo blob del cliente de almacenamiento.

        Retorna:
            BytesIO: El archivo blob como un objeto BytesIO.

        Lanza:
            ResourceNotFoundError: Si el blob no se encuentra en el almacenamiento.
            AttributeError: Si el cliente no tiene el atributo para descargar el blob.
        """
        try:            
            archivo_blob = self.cliente_storage.download_blob()
            archivo_blob_bytes = BytesIO(archivo_blob.readall())
            return archivo_blob_bytes
        except (ResourceNotFoundError, AttributeError):
            return BytesIO()

    def archivo_leer(self) -> DataFrame:
        """
        Lee un archivo parquet desde 'archivo_blob' y devuelve un pandas DataFrame.

        Parámetros:
            self.archivo_blob (str): La ruta al archivo parquet.

        Restorna:
            df (DataFrame): El archivo parquet cargado como un DataFrame de Pyspark.
            DataFrame: Un DataFrame vacío si no hay datos en el archivo parquet.
        """

        try:            
            df = pd.read_parquet(self.archivo_blob)
            return df
        except exceptions.NoDataError:
            return DataFrame()

    def archivo_subir(self, df: DataFrame, nombre_blob: str) -> None:
        """
        Sube un DataFrame de Pandas como un archivo Excel a un contenedor específico de Azure Blob Storage.

        Parámetros:
            df (Pandas_Dataframe): El DataFrame que se va a subir.
            nombre_blob (str): El nombre del blob que se va a crear.

        Restorna:
            None: Si la subida es exitosa.

        Lanza:
            exceptions.NoDataError: Si el DataFrame está vacío.
        """

        try:
            archivo_csv = BytesIO()
            df.index = df.index.astype(str)
            df.to_csv(archivo_csv)
            archivo_csv.seek(0)

            # Crear una nueva instancia de cliente storage con el container para los resultados
            cliente_storage_resultado = self.instancia_servicio_cliente.get_blob_client(
                self.container, nombre_blob, snapshot=None
            )

            if cliente_storage_resultado.exists():
                cliente_storage_resultado.delete_blob()
                cliente_storage_resultado.upload_blob(data=archivo_csv)
            else:
                cliente_storage_resultado.upload_blob(data=archivo_csv)
        except exceptions.NoDataError:
            return None

    def generar_archivo_excel_y_subir(self, diccionario_hojas, nombre_archivo):
        """
        Esta función toma un diccionario de DataFrames o Series y un nombre de archivo,
        y escribe cada DataFrame o Serie en una hoja separada de un archivo Excel.
        Luego sube el archivo a Azure Blob Storage.

        Parámetros:
            diccionario_hojas (dict): Un diccionario donde cada clave es el nombre de la hoja,
                                    y cada valor es un DataFrame o Serie.
            nombre_archivo (str): El nombre del archivo Excel que se creará.
            cliente_azure (ClienteAzure): Una instancia de la clase ClienteAzure.

        Retorna:
            None
        """
        # Crear un buffer en memoria para el archivo Excel
        excel_buffer = BytesIO()

        # Escribir DataFrames o Series en el buffer
        with ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            for nombre_hoja, datos in diccionario_hojas.items():
                if isinstance(datos, Series):
                    # Si los datos son una Serie, conviértelos en un DataFrame
                    datos = datos.to_frame()
                datos.to_excel(writer, sheet_name=nombre_hoja, index=False)

        # Rebobinar el buffer al inicio
        excel_buffer.seek(0)

        # Crear una nueva instancia de cliente storage con el container para los resultados
        cliente_storage_resultado = self.instancia_servicio_cliente.get_blob_client(
            self.container, nombre_archivo, snapshot=None
        )

        if cliente_storage_resultado.exists():
            cliente_storage_resultado.delete_blob()
            cliente_storage_resultado.upload_blob(data=excel_buffer)
        else:
            cliente_storage_resultado.upload_blob(data=excel_buffer)
        return None

    def archivo_blob_borrar(self) -> None:
        """
        Elimina un archivo blob del almacenamiento.

        Restorna:
            None
        """
        self.cliente_storage.delete_blob()

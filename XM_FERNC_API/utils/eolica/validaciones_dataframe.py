import pandas as pd
from XM_FERNC_API.utils.mensaje_constantes import MensajesEolica
from XM_FERNC_API.utils.manipulador_excepciones import CalculoExcepcion
from pyspark.sql.functions import col

def validar_presion_atmosferica(df: pd.DataFrame) -> None:
    """
    Esta función verifica que el DataFrame no tenga valores de presión atmosférica superiores a 3000 en la columna 
    "PresionAtmosferica".

    Parametros:
    df: Dataframe a validar
    """    
    if isinstance(df, pd.DataFrame):
        hay_error:bool = df[df["PresionAtmosferica"] >= 3000].shape[0] > 0
    else:
        hay_error:bool = df.filter(col("PresionAtmosferica") >= 3000).count()
    
    if hay_error:
        raise CalculoExcepcion(
            "Valor no permitido para presión atmosférica en df",
            "Validando Información",
            MensajesEolica.Error.ATMOSFERA_DATAFRAME.value
        )

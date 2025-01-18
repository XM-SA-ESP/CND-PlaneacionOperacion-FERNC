import numpy as np
import pandas as pd

from typing import Dict, Tuple
from XM_FERNC_API.utils.decoradores import capturar_excepciones

from XM_FERNC_API.utils.eolica.distancia import haversine
from XM_FERNC_API.utils.manipulador_excepciones import CalculoExcepcion
from XM_FERNC_API.utils.mensaje_constantes import MensajesEolica
from pyspark.sql import SparkSession
from functools import reduce
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, DoubleType
from pyspark.sql import Window
from pyspark.sql.functions import row_number, lit, expr, col, sum as py_sum


class Ordenamiento:

    def _organizacion(
        self, lat_t1: float, lon_t1: float, tj_longitud: np.array, tj_latitud: np.array
    ) -> Tuple[np.array, np.array]:
        """
        Metodo privado para obtener longitud_m y latitud_m que seran usados en para calcular
        el factor de ordenamiento.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - lat_t1 (float): Latitud del aerogenerador i.
        - lon_t1 (float): Longitud del aerogenerador i.
        - tj_longitud (np.array): Vector que contiene la longitud de los aerogeneradores.
        - tj_latitud (np.array): Vector que contiene las latitudes de los aerogeneradores.

        Retorno:
        - Tuple: Tupla que contiene:
            - longitud_m.
            - latitud_m.
        """
        # Misma latitud, diferente longitud
        x = haversine(lat1=lat_t1, lon1=lon_t1, lat2=lat_t1, lon2=tj_longitud) # [km]

        # Diferente latitud, misma longitud
        y = haversine(lat1=lat_t1, lon1=lon_t1, lat2=tj_latitud, lon2=lon_t1) # [km]

        # Signo de la resta
        sign_x = np.sign(tj_longitud - lon_t1)
        sign_y = np.sign(tj_latitud - lat_t1)

        return sign_x * x * 1000, sign_y * y * 1000 # (x_m, y_m) [km])
    
    def _recorrer_estampas(self, i: int, aux_latitud, aux_longitud, dir_promedio, parque_reorganizado) -> None:
        """
        Distancia 2D respecto a la primera turbina
        """
        lat_t1 = aux_latitud[0]
        lon_t1 = aux_longitud[0]

        longitud_m, latitud_m = self._organizacion(
            lat_t1=lat_t1, lon_t1=lon_t1, tj_longitud=aux_longitud, tj_latitud=aux_latitud
        )

        parque_reorganizado = parque_reorganizado.withColumn("longitud_m", lit(longitud_m))
        parque_reorganizado = parque_reorganizado.withColumn("latitud_m", lit(latitud_m))

        theta_j = (90 - dir_promedio[i]) * (np.pi / 180)  # Valor en Radianes
        parque_reorganizado = parque_reorganizado.withColumn("theta_j", lit(theta_j))


        parque_reorganizado = parque_reorganizado.withColumn(
                "factor_reordenamiento",
            expr("transform(longitud_m, (x, i) -> SIN(theta_j) * x + COS(theta_j) * latitud_m[i])")
        )

        # Ordenar el DataFrame por factor_reordenamiento en orden descendente
        parque_reorganizado = parque_reorganizado.orderBy(parque_reorganizado["factor_reordenamiento"].desc())
        

        # Agregar una nueva columna de índice incremental
        window = Window.orderBy("factor_reordenamiento")
        parque_reorganizado = parque_reorganizado.withColumn("new_index", row_number().over(window))

        # Eliminar la columna de índice original
        parque_reorganizado = parque_reorganizado.drop("index")

        # Renombrar la columna de índice nuevo como "index" y ajustar el índice
        parque_reorganizado = parque_reorganizado.withColumnRenamed("new_index", "index").select("index", "*")


        # parque_reorganizado.set_index("id_turbina", inplace=True)
        return parque_reorganizado
    
    
    @capturar_excepciones(
            MensajesEolica.Estado.ORDENAMIENTO.value,
            MensajesEolica.Error.ORDENAMIENTO.value,
            CalculoExcepcion
    )
    def ordenamiento_vectorizado_pyspark(self, aerogeneradores: Dict, n_estampas: int, ss: SparkSession) -> Dict:
        """
        Calculo vectorizado del ordenamiento para las estampas de tiempo. Retorna un diccionario con las estampas como
        key y dataframes como values con la informacion para esa estampa.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - aerogeneradores (Dict): Diccionario que mapea identificadores de aerogeneradores a objetos de aerogeneradores.
        - n_estampas (int): Numero de estampas de tiempo.

        Retorno:
        - direcciones_por_estampa (Dict): Diccionario con Pandas DatetimeIndex como keys y Dataframe como values.
        """
        # Configuración del parque en DataFrame
        aux_longitud = np.array([i.longitud for i in aerogeneradores.values()])
        aux_latitud = np.array([i.latitud for i in aerogeneradores.values()])
        # Seleccionar las columnas de longitud y latitud del DataFrame df_aerogeneradores
        #aux_longitud = df_aerogeneradores.select("longitud").rdd.flatMap(lambda x: x).collect()
        #aux_latitud = df_aerogeneradores.select("latitud").rdd.flatMap(lambda x: x).collect()



        lista_aero_df = [aero.df for aero in aerogeneradores.values()]        
        # Dataframe auxiliar con shape n estampas por n aerogeneradores
        #aux_df = pd.concat(lista_aero_df, axis=1)["DireccionViento"]
        aux_df = reduce(lambda df1, df2: df1.union(df2), lista_aero_df).select("DireccionViento")       
        aux_df.show(5)
        dir_promedio = aux_df.select("DireccionViento").rdd.flatMap(lambda x: x).collect()

        datos = [(aero.id_aero, aero.elevacion) for aero in aerogeneradores.values()]
        schema = StructType([
            StructField("id_turbina", IntegerType(), True),
            StructField("Elevacion_m", DoubleType(), True)
        ])
        parque_reorganizado = ss.createDataFrame(datos, schema)

        print("PASO 6")
        direcciones_por_estampa = {}
        for i in range(n_estampas):
            parque_reorganizado_estampa = self._recorrer_estampas(i, aux_latitud, aux_longitud, dir_promedio, parque_reorganizado)
            direcciones_por_estampa[dir_promedio[i]] = parque_reorganizado_estampa.collect()

        return direcciones_por_estampa
    
    @capturar_excepciones(
            MensajesEolica.Estado.ORDENAMIENTO.value,
            MensajesEolica.Error.ORDENAMIENTO.value,
            CalculoExcepcion
    )
    def ordenamiento_vectorizado(self, aerogeneradores: Dict, n_estampas: int, pd_type = True) -> Dict:
        """
        Calculo vectorizado del ordenamiento para las estampas de tiempo. Retorna un diccionario con las estampas como
        key y dataframes como values con la informacion para esa estampa.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - aerogeneradores (Dict): Diccionario que mapea identificadores de aerogeneradores a objetos de aerogeneradores.
        - n_estampas (int): Numero de estampas de tiempo.

        Retorno:
        - direcciones_por_estampa (Dict): Diccionario con Pandas DatetimeIndex como keys y Dataframe como values.
        """        
        # Configuración del parque en DataFrame
        aerogeneradores_values = list(aerogeneradores.values())
        aux_longitud = np.array([aero.longitud for aero in aerogeneradores_values])
        aux_latitud = np.array([aero.latitud for aero in aerogeneradores_values])
        direcciones_por_estampa = {}
        # Dataframe auxiliar con shape n estampas por n aerogeneradores
        if pd_type:            
            aux_df = pd.concat([aero.df for aero in aerogeneradores_values], axis=1)["DireccionViento"]
            index_list = list(aux_df.index)
            dir_promedio = aux_df.mean(axis=1).to_numpy()
            theta = (90 - dir_promedio) * (np.pi / 180)
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)
            
        
        lat_t1, lon_t1 = aux_latitud[0], aux_longitud[0]
        id_turbina = np.array([aero.id_aero for aero in aerogeneradores_values])
        elevacion = np.array([aero.elevacion for aero in aerogeneradores_values])

        longitud_m, latitud_m = self._organizacion(
            lat_t1=lat_t1, lon_t1=lon_t1, tj_longitud=aux_longitud, tj_latitud=aux_latitud
        )
        direcciones_por_estampa = {} 
        if pd_type:
            base_df = pd.DataFrame({
                "id_turbina": id_turbina,
                "Elevacion_m": elevacion,
                "longitud_m": longitud_m,
                "latitud_m": latitud_m
            })            
            
            for i in range(n_estampas):
                factor_reordenamiento = sin_theta[i] * longitud_m + cos_theta[i] * latitud_m
                base_df["factor_reordenamiento"] = factor_reordenamiento
                parque_reorganizado = base_df.sort_values(by="factor_reordenamiento", ascending=False).reset_index(drop=True)
                
                parque_reorganizado.index += 1                
                direcciones_por_estampa[index_list[i]] = parque_reorganizado
          
        
        return direcciones_por_estampa
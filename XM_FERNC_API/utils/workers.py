import pandas as pd
from pyspark.sql.functions import pandas_udf, PandasUDFType
from XM_FERNC_API.utils.eolica.funciones_correccion_velocidad_parque_eolico import (
    CorreccionVelocidadParque,
    correccion_velocidad_parque_eolico_solo
)
from XM_FERNC_API.utils.eolica.caracterizacion_estela import efecto_estela_vectorizado_refactor
import pandas as pd
from pyspark.sql.functions import pandas_udf, PandasUDFType
from pyspark.sql.types import StructField, StringType, IntegerType, ArrayType, StructType, MapType, DoubleType
import numpy as np
from pyspark.sql import SparkSession



# Define the schema

schema = ArrayType(StructType([
        StructField("fech", StringType(), True),
        StructField("aero_id", IntegerType(), True),
        StructField("vel_corregida", DoubleType(), True)
]))



def new_correcction(args_list_df, aerogeneradores_broadcast, modelos_broadcast):    
    @pandas_udf(schema)
    def correcciones_worker_udf(fecha: pd.Series, ordenamiento: pd.Series, h_buje_promedio: pd.Series, z_o1: pd.Series, z_o2: pd.Series) -> pd.Series:
        
        results = []
        
        for i in range(fecha.shape[0]):
            vel_aero_list_3 = []
            fech = fecha[i]
            orden = ordenamiento[i]
            h_buje = h_buje_promedio[i] 
            z1 = float(str(z_o1[i]))
            z2 = float(str(z_o2[i]))              
            

            vel_aero_list = correccion_velocidad_parque_eolico_solo(
                fech,
                orden,
                aerogeneradores_broadcast.value,
                modelos_broadcast.value,
                h_buje,
                z1,
                z2,
            )
            if vel_aero_list is not None:                     
                for vel, aero in vel_aero_list:
                    vel_aero_list_3.append((fech,aero, vel))
            else:
                vel_aero_list_3.append((fech,None, None))            
            results.append(vel_aero_list_3)


        return pd.Series(results)

    temp = args_list_df.withColumn("result", correcciones_worker_udf("fecha", "ordenamiento", "h_buje_promedio", "offshore", "z_o1", "z_o2")).select("result")    
    result_array= temp.collect()    
    return result_array


def wrapper_efecto_estela_vectorizado(offshore, cre, caracteristicas_tij, n_turbinas, df_data, curvas_info):

    @pandas_udf(ArrayType(DoubleType()))
    def vectorized_udf(keys: pd.Series, 
                    turbine_info:pd.Series,
                    estructura_info: pd.Series,
                    densidades:pd.Series) -> pd.Series:
        result = []
        for i in range(keys.shape[0]):
            densidad = densidades.iloc[i]
            estela_result = efecto_estela_vectorizado_refactor(
                                                            offshore, 
                                                            cre,
                                                            densidad,  
                                                            turbine_info.iloc[i],
                                                            estructura_info.iloc[i],
                                                            n_turbinas,
                                                            caracteristicas_tij,
                                                            curvas_info
                                                        )

            result.append(estela_result)
        return pd.Series(result)
    spark = SparkSession.builder.getOrCreate() ##
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")##
    result = df_data.withColumn("result", vectorized_udf("key", "turbine_info", "estructura_info",  "densidad")).select("result").collect()
    velocidades_estela = [np.array(row.result) for row in result]


    return velocidades_estela

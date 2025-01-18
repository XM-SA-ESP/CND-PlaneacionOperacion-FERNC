import os
import sys
import functools
import multiprocessing

import polars as pl
import pandas as pd
import numpy as np
import xarray as xr

from typing import Dict, List, Tuple

from XM_FERNC_API.infraestructura.models.eolica.parametros import (
    JsonModelEolica,
    ParametrosTransversales,
)
from XM_FERNC_API.infraestructura.models.respuesta import Respuesta, Resultado
from XM_FERNC_API.dominio.servicio.azure_blob.cliente_azure import ClienteAzure

from XM_FERNC_API.utils import workers
from XM_FERNC_API.utils.decoradores import capturar_excepciones
from XM_FERNC_API.utils.mensaje_constantes import MensajesEolica
from XM_FERNC_API.utils.consumidor import ConsumirApiEstado
from XM_FERNC_API.utils.estructura_xarray import (
    crear_estructura_xarray_vectorizado,
    crear_estructura_curvas_xarray
)
from XM_FERNC_API.utils.manipulador_excepciones import BaseExcepcion, CalculoExcepcion, ManipuladorExcepciones
from XM_FERNC_API.utils.manipulador_dataframe import ManipuladorDataframe
from XM_FERNC_API.utils.manipulador_modelos import ManipuladorModelos
from XM_FERNC_API.utils.eolica.manipulador_estructura import ManipuladorEstructura
from XM_FERNC_API.utils.eolica.funciones_calculo_temp_presion_densidad import (
    CalculoTempPresionDensidad,
)
from XM_FERNC_API.utils.eolica.funciones_corregir_curvas import CorregirCurvas
from XM_FERNC_API.utils.eolica.funciones_calculo_pcc import CalculoPcc
from XM_FERNC_API.utils.eolica.funciones_ordenamiento import Ordenamiento
from XM_FERNC_API.utils.eolica.funciones_correccion_velocidad_parque_eolico import (
    CorreccionVelocidadParque,
    serialize_aerogenerador,
    serialize_modelo
)
from XM_FERNC_API.utils.eolica.ajuste_potencia import potencia_vectorizado, potencia_vectorizado_udf
from XM_FERNC_API.utils.eolica.dataclasses_eolica import Torre
from XM_FERNC_API.utils.generar_archivo_excel import GenerarArchivoExcel
from XM_FERNC_API.dominio.servicio.pyspark_service.pyspark_session import generar_sesion
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, pandas_udf, PandasUDFType
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, FloatType, BooleanType, IntegerType, DoubleType, MapType
from pyspark.sql.functions import udf
from pyspark.sql import Row
import time
from logging import INFO, getLogger, StreamHandler, Formatter
from azure.monitor.opentelemetry import configure_azure_monitor
from pyspark.sql import SparkSession
def timer(start,end):
   hours, rem = divmod(end-start, 3600)
   minutes, seconds = divmod(rem, 60)
   return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)
from XM_FERNC_API.utils.databricks_logger import DbLogger, timer


def convert_xarray(xarra, time):
    ds_dict = xarra.sel(tiempo=time).to_dict()

    # Manually reformat the dictionary to use lists
    def reformat_dict(d):
        if isinstance(d, dict):
            if 'data' in d:
                return d['data']
            return {k: reformat_dict(v) for k, v in d.items()}
        return d

    # Apply the reformatting
    reformatted_ds_dict = {k: reformat_dict(v) for k, v in ds_dict['data_vars'].items()}
    return reformatted_ds_dict

arg_list_schema = StructType([
    StructField("fecha", StringType(), True),
    StructField("ordenamiento", ArrayType(IntegerType()), True),
    StructField("h_buje_promedio", DoubleType(), True),
    StructField("offshore", BooleanType(), True),
    StructField("z_o1", DoubleType(), True),
    StructField("z_o2", DoubleType(), True)
    ])

xarray_schema = StructType([
    StructField("temperatura_ambiente", ArrayType(DoubleType())),
    StructField("velocidad_estela", ArrayType(DoubleType())),
    StructField("velocidad_viento", ArrayType(DoubleType())),
    StructField("velocidad_grandes_parques", ArrayType(DoubleType()))
    ])

potencia_schema = StructType([
    StructField("key", StringType(), True),
    StructField("estructura_x_info", xarray_schema, True),          
    StructField("densidad", ArrayType(DoubleType()))
    ])

class ServicioEolicas:
    
    def __init__(self) -> None:
        self.manipulador_df = ManipuladorDataframe()
        self.manipulador_modelos = ManipuladorModelos()
        self.manipulador_estructura = ManipuladorEstructura()
        self.calculo_temp_presion_densidad = CalculoTempPresionDensidad()
        self.ajuste_curvas = CorregirCurvas()
        self.calculo_pcc = CalculoPcc()
        self.ordenamiento = Ordenamiento()
        self.correccion_parques = CorreccionVelocidadParque()
        self.generar_archivo = GenerarArchivoExcel(self.manipulador_df, 1)

        self.cliente_azure = None
        self.sesion_spark = generar_sesion()
        
        self.logger_info = DbLogger('info')


    def ejecutar_calculos(self, params: JsonModelEolica):
        """
        Método principal que ejecuta los cálculos y arroja los resultados del proceso completo para plantas eólicas.
        El proceso tiene 2 posibilidades de ejecución:
            1. Cuando se tiene información medida, deben existir por obligatoriedad sistemas de medición (Torres) y cada sistema de medición tiene su propio archivo de series.
            2. Cuando no se tiene información medida, es decir, sin sistema de medición se envía un único archivo de series.
        A partir de los archivos de series y demás valores del objeto se obtiene los resultados esperados.

        Params:
            -params: Modelo que representa el objeto completo requerido para calculos de las plantas eólicas generado por la aplicación.

        Retorna:
            resultado: Objeto de tipo Respuesta que contiene el resultado final de la EDA, la lista de valores de la ENFIC por cada periodo de la serie y el nombre del archivo
            subido al blob storage con todos los resultados por cada fila de las series cargadas según sea el caso.
        """
        self.logger_info.initialize_logger()
        
        print(f"Nombre planta: {params.ParametrosTransversales.NombrePlanta}")

        DESCRIPCION = "Descripción"
        ID_CONEXION = params.IdConexionWs
        cae_instancia = ConsumirApiEstado(
            proceso="EstadoCalculo", conexion_id=ID_CONEXION, pasos_totales=6
        )
        params_trans = params.ParametrosTransversales
        offshore = params_trans.Offshore        
        promedio_ohm = self.__obtener_promedio_resistencia(params)
        z_o1, z_o2, cre = self.__obtener_z_cre_values(offshore)

        try:
            start_global = time.time()
            print("params_trans.InformacionMedida")
            print(params_trans.InformacionMedida)
            if params_trans.InformacionMedida:                
                params, torres = self.actualizar_aerogenerador_a_torre_cercana(params)                
                modelos, aerogeneradores = (
                    self.manipulador_estructura.crear_dict_modelos_aerogeneradores(
                        params
                    )
                )
                torres = self.ejecutar_calculo_temperatura_presion_densidad(
                    torres
                )
                serie_tiempo = self.manipulador_df.obtener_serie_tiempo_eolica(
                    torres=torres
                )

                cae_instancia.consumir_api_estado(
                    MensajesEolica.Estado.CURVAS.value, True
                )
                self.ajuste_curvas.corregir_curvas_con_torre(
                    torres, modelos, aerogeneradores
                )
                aerogeneradores = self.manipulador_estructura.agregar_pcc(
                    params, aerogeneradores
                )
                aerogeneradores = self.calculo_pcc.calculo_pcc_aerogenerador(
                    params, aerogeneradores
                )

                aerogeneradores = self.__asignar_df_aerogeneradores(
                    aerogeneradores, torres
                )

            else:
                df = self.generar_dataframe(params.ArchivoSeries.Nombre)
                modelos, aerogeneradores = (
                    self.manipulador_estructura.crear_dict_modelos_aerogeneradores(
                        params
                    )
                )
                
                diccionario_resultado = (
                    self.ejecutar_calculo_temperatura_presion_densidad(
                        dataframe=df
                    )
                )
                df = diccionario_resultado["dataframe"]
                serie_tiempo = self.manipulador_df.obtener_serie_tiempo_eolica(df=df)
                
                self.ajuste_curvas.corregir_curvas_sin_torres(df, modelos, aerogeneradores)
                
                aerogeneradores = self.manipulador_estructura.agregar_pcc(
                    params, aerogeneradores
                )
                aerogeneradores = self.calculo_pcc.calculo_pcc_aerogenerador(
                    params, aerogeneradores
                )
                aerogeneradores = self.__asignar_df_aerogeneradores(
                    aerogeneradores, df=df
                )


            print("Ordenamiento")
            cae_instancia.consumir_api_estado(
                MensajesEolica.Estado.ORDENAMIENTO.value, True
            )
            start = time.time()                        
            dict_ordenamiento = self.ordenamiento.ordenamiento_vectorizado(
                aerogeneradores, len(serie_tiempo), self.sesion_spark
            )                                  
    
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Ordenamiento ", start)            

            
            print("Correccion parques")
            cae_instancia.consumir_api_estado(MensajesEolica.Estado.PARQUES.value, True)            
            start = time.time()
            
            caracteristicas_df = self.__caracteristicas_tij(aerogeneradores, modelos)

            estructura_xarray = self.__estructura_xarray_vectorizado(aerogeneradores, serie_tiempo)            
            if offshore:
                aerogeneradores_serialized = {key: serialize_aerogenerador(value) for key, value in aerogeneradores.items()}
                aerogeneradores_broadcast = self.sesion_spark.sparkContext.broadcast(aerogeneradores_serialized)
                modelos_serialized = {key: serialize_modelo(value) for key, value in modelos.items()}
                modelos_broadcast = self.sesion_spark.sparkContext.broadcast(modelos_serialized)
                lista_ordenamiento = []


                for df in dict_ordenamiento.values():
                    lista_ordenamiento.append(df["id_turbina"].to_list())                
                h_buje_promedio = self.correccion_parques.calcular_h_buje_promedio(
                    modelos, aerogeneradores
                )                
                
                args_list = self.__crear_lista_argumentos_correcciones(
                    h_buje_promedio,
                    offshore,
                    z_o1,
                    z_o2,
                    serie_tiempo,
                    lista_ordenamiento,
                )
                args_list_df = self.sesion_spark.createDataFrame(args_list, arg_list_schema)
                result_array= workers.new_correcction(args_list_df, aerogeneradores_broadcast, modelos_broadcast)                
                for row in result_array:
                    self.__asignar_valores_aerogeneradores(
                        row['result'], aerogeneradores, columna="VelocidadViento"
                    )                    
                vectores_velocidades = self.__crear_lista_vectores_velocidades(aerogeneradores, serie_tiempo)
                data = np.array(vectores_velocidades).T
              
            else:
                data = estructura_xarray["velocidad_viento"].values
           

            estructura_xarray["velocidad_grandes_parques"] = (
                ["turbina", "tiempo"],
                data,
                {
                    "Descripción": "Velocidad del viento perturbada por efecto de grandes parques en [m/s]."
                }
            )
            
            n_turbinas = len(aerogeneradores.keys())
            curvas_xarray = self.__estructura_xarray_curvas(aerogeneradores)

            direccion_viento_t = estructura_xarray['direccion_viento'].values
            velocidad_grandes_parques_t = estructura_xarray['velocidad_grandes_parques'].values
            velocidad_viento_t = estructura_xarray['velocidad_viento'].values
            
            dict_keys = list(dict_ordenamiento.keys())
            # Use a list comprehension directly to create the list of dictionaries
            def create_estructura_info(index):
                return {"direccion_viento": direccion_viento_t.T[index].tolist(),
                        "velocidad_viento": velocidad_viento_t.T[index].tolist(),
                        "velocidad_grandes_parques":  velocidad_grandes_parques_t.T[index].tolist()}

            dict_keys = list(dict_ordenamiento.keys())
            densidad = pd.DataFrame(
                {key: value.df["DenBuje"] for key, value in aerogeneradores.items()}
            ) 


            data = [[str(val), dict_ordenamiento[val].to_dict(orient='list'), create_estructura_info(i), list(densidad.loc[val])]for i, val in enumerate(dict_keys)] ## slow, optim 297 - 319 
            turbine_info = StructType([StructField("Elevacion_m", ArrayType(DoubleType())),
                                        StructField("factor_reordenamiento", ArrayType(DoubleType())),
                                        StructField("latitud_m", ArrayType(DoubleType())),
                                        StructField("longitud_m", ArrayType(DoubleType())),
                                        StructField("id_turbina", ArrayType(IntegerType()))])

            estructura_info = StructType([StructField("direccion_viento", ArrayType(DoubleType())),
                                        StructField("velocidad_viento", ArrayType(DoubleType())),
                                        StructField("velocidad_grandes_parques", ArrayType(DoubleType()))])



            schema = StructType([StructField("key", StringType(), True),
                    StructField("turbine_info", turbine_info, True),
                    StructField("estructura_info", estructura_info, True),
                    StructField("densidad", ArrayType(DoubleType()))])
                    #StructField("estructura_info", estructura_info, True)])

            df_data = self.sesion_spark.createDataFrame(data, schema)  
            
                                 
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Correccion parques ", start)
            print("Estela")
            cae_instancia.consumir_api_estado(MensajesEolica.Estado.ESTELA.value, True)
            start = time.time()

            curvas_info = {'cur_vel': curvas_xarray['cur_vel'].values,
                                    'cur_coef': curvas_xarray['cur_coef'].values}

            velocidades_estela = workers.wrapper_efecto_estela_vectorizado(
                offshore,
                cre,
                caracteristicas_df,         
                n_turbinas,
                df_data,
                curvas_info
            )

            estructura_xarray["velocidad_estela"] = (
                ["turbina", "tiempo"],
                np.array(velocidades_estela).T,
                {
                    DESCRIPCION: "Velocidad del viento perturbada por efecto estela en [m/s]."
                },
            )
            
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Estela ", start)
            xarray_keys = list(estructura_xarray.tiempo.values)
            data_xarray = [[str(val), convert_xarray(estructura_xarray, val), list(densidad.loc[val])]for i, val in enumerate(xarray_keys)]
            potencia_data_df = self.sesion_spark.createDataFrame(data_xarray, potencia_schema)
            print("Potencia")
            start = time.time()

            cae_instancia.consumir_api_estado(
                MensajesEolica.Estado.POTENCIA.value, True
            )

            
            estructura_xarray = self.__calculo_potencia_vectorizado(
                potencia_data_df,
                caracteristicas_df,
                estructura_xarray,                
                curvas_xarray,
                params_trans,
                promedio_ohm
            )
            cae_instancia.consumir_api_estado(
                MensajesEolica.Estado.POTENCIA.value, True
            )

            estructura_xarray["potencia_parque"] = (
                ["tiempo"],
                estructura_xarray["potencia"].sum(axis=0).values,
                {DESCRIPCION: "Potencia AC del parque eólico en [kW]."},
            )

            energia_planta = self.__crear_df_energia_planta(
                estructura_xarray, serie_tiempo
            )
            energia_planta = energia_planta.clip(upper=params_trans.Ppi/1000)
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Potencia ", start)           

            nombre_archivo_resultado = (
                os.path.splitext(params.ArchivoSeries.Nombre)[0] + "_resultado.xlsx"
            )
            energia_al_mes = self.manipulador_df.filtrar_por_mes(energia_planta)
            energia_diaria = self.manipulador_df.filtrar_por_dia(energia_al_mes)
            resultado_enficc = self.calcular_enficc(params_trans, energia_diaria)
            resultado_eda = self.manipulador_df.calcular_eda(
                params_trans, energia_diaria, resultado_enficc
            )

            resultado_enficc.valor = round(resultado_enficc.valor)

            self.generar_archivo.generar_archivo_excel(
                energia_planta=energia_planta,
                energia_mes=energia_al_mes,
                energia_diaria=energia_diaria,
                enficc=resultado_enficc,
                eda=resultado_eda,
                nombre_archivo=nombre_archivo_resultado,
            )
            resultado = Respuesta(
                nombre_archivo_resultado, [resultado_enficc], resultado_eda
            )
            
            print("TIEMPO TOTAL: ", timer(start_global, time.time()))
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " TIEMPO TOTAL:  ", start)           
            return resultado
        except BaseExcepcion as e:            
            print("ERROR BaseExcepcion")
            print(e)
            return ManipuladorExcepciones(e.error, e.tarea, e.mensaje)
        except Exception as e:
            print("ERROR Exceptions")
            print(e)
            return ManipuladorExcepciones(e, "Ejecutando Calculos.", "Error no controlado.")

    def generar_dataframe(self, nombre_blob: str) -> DataFrame:
        """
        Genera un dataframe usando el nombre del blob.
        Args:
            nombre_blob (str): Nombre del blob.
        Retorna:
            pl.DataFrame: El dataframe Polars generado.
        """
        df = pd.read_parquet(os.environ['VOLUME'] + nombre_blob)
        spark = SparkSession.builder.getOrCreate()
        if 'PYTEST_CURRENT_TEST' not in os.environ:
            from pyspark.dbutils import DBUtils
            dbutils = DBUtils(spark)
            dbutils.fs.rm(os.environ['VOLUME'] + nombre_blob)

        return df

    def actualizar_aerogenerador_a_torre_cercana(self, params: JsonModelEolica) -> tuple:
        """
        Genera un tuple que contiene los params actualizados apuntando a las torres correctas y 
        un diccionario que contiene la id de las torres como key y las especificaciones como value

        Args:
            params: Objeto que contiene la informacion del JSON

        Retorna:
            tuple:
                - params (JsonModelEolica): Objeto actualizado con torres ajustadas.
                - torres (Dict): Diccionario con la informacion de las torres.
        """
        torres = self.crear_dict_torres(params)
        self.manipulador_modelos.ajustar_aerogeneradores(params, torres)

        return params, torres

    def ejecutar_calculo_temperatura_presion_densidad(
        self,
        torres: Dict | None = None,
        dataframe: pl.DataFrame | None = None,
    ) -> Dict:
        """
        Calculo de la temperatura, presion atmosferica y densidad a la altura del buje para las series
        asociadas a las torres o, en el caso de que no cuente con sistema de medicion, a la unica serie.

        Args:
            - modelos (Dict): Diccionario con la informacion de los modelos.
            - aerogeneradores (Dict): Diccionario con la informacion de los aerogewneradores.
            - torres (Dict): Diccionario con la informacion de las torres.
            - dataframe (pd.Dataframe): Pandas dataframe de la unica serie.
        
        Retorna:
            - resultado (Dict): Diccionario con los resultados para cada torre o con un 
            unico registro si no cuenta con sistema de medicion. 
        """
        resultado = (
            self.calculo_temp_presion_densidad.calculo_temperatura_presion_densidad(
                torres, dataframe
            )
        )

        return resultado

    def crear_dict_torres(self, params: JsonModelEolica) -> Dict:
        """
        Genera un diccionario con la informacion de las torres

        Args:
            params: Objeto que contiene la informacion del JSON.

        Retorna:
            torres_dict (Dict): Diccionario con la informacion de las torres.
        """
        torres_dict = {}

        for torre in params.ParametrosConfiguracion.SistemasDeMedicion:
            torre_id = torre.IdentificadorTorre
            df = self.generar_dataframe(torre.ArchivoSeriesRelacionado)
            df = self.manipulador_df.ajustar_df_eolica(df)

            torres_dict[torre_id] = Torre(
                torre_id,
                torre.Latitud,
                torre.Longitud,
                torre.Elevacion,
                torre.RadioRepresentatividad,
                torre.ConfiguracionAnemometro,
                torre.ArchivoSeriesRelacionado,
                df,
            )

        return torres_dict
    def process_pandas_df(self, aero, df):
        aero.df = df.copy()
        aero.df["VelocidadEstela"] = aero.df["VelocidadViento"]

    def process_spark_df(self, aero, df):
        aero.df = df.withColumn("VelocidadEstela", col("VelocidadViento"))    

    def __asignar_df_aerogeneradores(
        self, aerogeneradores: Dict, torres: Dict | None = None, df: pd.DataFrame | None = None
    ) -> Dict:
        """
        Asigna un dataframe a cada aerogenerador.

        Params:
            aerogeneradores (Dict): Diccionario con los aerogeneradores.
            torres (Dict, optional): Diccionario de las torres. Si es provisto, 
            el dataframe de cada aerogenerador sera copiado y asignado de la torre.
            df (DataFrame, optional): Un dataframe que sera copiado a cada aerogenerador.

        Retorna:
            Dict: Un diccionario actualizado con los aerogeneradores y su dataframe respectivo.
        """
        if torres:
            for aero in aerogeneradores.values():
                aero.df = torres[aero.id_torre].dataframe.copy()
                aero.df["VelocidadEstela"] = aero.df["VelocidadViento"]
        else:
            for aero in aerogeneradores.values():
                aero.df = df.copy()
                aero.df["VelocidadEstela"] = aero.df["VelocidadViento"]
        return aerogeneradores       

    def __obtener_z_cre_values(self, offshore: bool) -> tuple:
        """
        Obtencion de los parametros z_o1, z_o2 y cre en base al parametro offshore

        Params:
            -offshore: Boolean que indica si el parametro offshore es True o False.

        Retorna:
            - z_o1: Rugosidad del terreno
            - z_o2: Rugosidad aumentada por el parque
            - cre: Constante que depende de offshore
        """
        if offshore:
            return 0.0002, 0.03, 0.04
        else:
            return 0.055, 0.05, 0.075

    def calcular_enficc(
        self, params_trans: ParametrosTransversales, energia_diaria_df
    ) -> Resultado:
        """
        Método para calcular la energía firme de la planta eólica, como valor minimo entre Em(energía firme diaria) y la ecuación 24*CEN*(1-IHF)*1000.
        En caso tal y la planta no cuente con información medida, el valor de Em se debe multiplicar por 0.6
        Params:
            -params_trans: Modelo de representación de los parametros transversales que llegan de la aplicación
            -energia_diaria_df: Diccionario de datos con el valor de la energía firme diario a partir de la energía mensual de la planta
            
        Retorna:
            resultado: objeto de Tipo Resultado con el valor de la energía firme por año y mes.
        """
        valor_minimo_diario = energia_diaria_df["diaria"].min()
        fecha_minimo_diario = energia_diaria_df[
            energia_diaria_df["diaria"] == valor_minimo_diario
        ].index[0]
        energia_calculada = (
            24 * params_trans.Cen * (1 - (params_trans.Ihf / 100)) * 1000
        )
        energia_firme = min(valor_minimo_diario, energia_calculada)
        # En caso de que la planta NO cuente con información medida
        if not params_trans.InformacionMedida:
            energia_firme *= 0.6
        resultado = Resultado(
            anio=int(fecha_minimo_diario.year),
            mes=int(fecha_minimo_diario.month),
            valor=energia_firme,
        )
        return resultado

    def __crear_lista_argumentos_correcciones(
        self,
        h_buje_promedio: np.float64,
        offshore: bool,
        z_o1: float,
        z_o2: float,
        serie_tiempo: pd.DatetimeIndex,
        lista_ordenamiento: List,
    ) -> List:
        """
        Genera una lista de argumentos que seran consumidos por el worker en el multiproceso

        Args:
            - aerogeneradores (Dict): Diccionario que contiene la informacion de los aerogeneradores.
            - modelos (Dict): Diccionario que contiene la informacion de los modelos.
            - h_buje_promedio (float): Altura buje promedio.
            - offshore (bool): Parametro offshore del JSON.
            - z_o1 (float): Rugosidad del terreno.
            - z_o2 (float): Rugosidad aumentada por el parque.
            - serie_tiempo (pd.DatetimeIndex): Serie con las estampas de tiempo.
            - lista_ordenamiento (List): Ordenamiento de los aerogeneradores para esa fecha.
        Retorna:
            - args_list (List): Lista de argumentos para ser consumidos y usados en correcciones_worker
        """
        args_list = [
            (
                fecha.to_pydatetime().isoformat(),
                ordenamiento,
                float(h_buje_promedio),
                offshore,
                z_o1,
                z_o2,
            )
            for fecha, ordenamiento in zip(serie_tiempo, lista_ordenamiento)
        ]
        return args_list

    def __obtener_promedio_resistencia(self, params: JsonModelEolica) -> np.float64:
        """
        Genera un promedio de la resistencia de los cableados que sera usado
        en el calculo de potencia

        Args:
            - params (JsonModelEolica): Objeto que contiene la informacion del JSON
        Retorna:
            - promedio_ohm (float): Promedio de la resistencia del cableado en ohms
        """
        promedio_ohm = []
        for p in params.ParametrosConfiguracion.ParametroConexion:
            promedio_ohm.append(p.Resistencia)

        promedio_ohm = np.mean(promedio_ohm)
        return promedio_ohm

    @capturar_excepciones(
            MensajesEolica.Estado.CORRECCION_PARQUES.value,
            MensajesEolica.Error.PARQUES.value,
            CalculoExcepcion
    )
    def __asignar_valores_aerogeneradores(
        self, resultados, aerogeneradores: Dict, columna: str
    ) -> None:
        """
        Asigna los resultados obtenidos por los workers a los aerogeneradores correspondientes.

        Args:
            - resultados (Tupla): Lista que contiene la fecha y una lista con tuplas que contienen el id del aerogenerador y el valor a agregar.
            - aerogeneradores (Dict): Diccionario que contiene la informacion de los aerogeneradores.
            - columna (str): Nombre de la columna donde se actualizaran los valores.
        Retorna:
            - aerogeneradores (Dict): Diccionario de los aerogeneradores con sus dataframes actualizados.
        """
        for value in resultados:
            fecha, aero_id, v = value['fech'], value['aero_id'], value['vel_corregida']
            if v is not None:
                aerogeneradores[aero_id].df.at[fecha, columna] = v

    def __caracteristicas_tij(self, aerogeneradores: Dict, modelos: Dict):
        """
        Crea un Pandas DataFrame con las especificaciones para cada aerogenerador.

        Args:
            - aerogeneradores (Dict): Diccionario que contiene la informacion de los aerogeneradores.
            - modelos (Dict): Diccionario que contiene la informacion de los modelos.
        Retorna:
            - caracteristicas_df (pd.DataFrame): Dataframe de 8 columnas por x numero de aerogeneradores.
        """
        index = [aero.id_aero for aero in aerogeneradores.values()]
        
        elevacion = np.array([modelos[aero.modelo].altura_buje for aero in aerogeneradores.values()])
        diametro = np.array([modelos[aero.modelo].diametro_rotor for aero in aerogeneradores.values()])
        densidad = np.array([modelos[aero.modelo].den_nominal for aero in aerogeneradores.values()])
        distancia_pcc = np.array([aero.dist_pcc for aero in aerogeneradores.values()])
        t_minima = np.array([modelos[aero.modelo].t_min for aero in aerogeneradores.values()])
        t_maxima = np.array([modelos[aero.modelo].t_max for aero in aerogeneradores.values()])
        p_nominal = np.array([modelos[aero.modelo].p_nominal for aero in aerogeneradores.values()])
        
        radio = diametro / 2
        area_rotor = np.pi * (radio ** 2)
        
        # Creating the DataFrame directly using the arrays
        caracteristicas_df = pd.DataFrame({
            "altura_buje": elevacion,
            "radio": radio,
            "densidad": densidad,
            "area_rotor": area_rotor,
            "dist_pcc": distancia_pcc,
            "t_min": t_minima,
            "t_max": t_maxima,
            "p_nominal": p_nominal,
        }, index=index)

        return caracteristicas_df

    @capturar_excepciones(
            MensajesEolica.Estado.CORRECCION_PARQUES.value,
            MensajesEolica.Error.PARQUES.value,
            CalculoExcepcion
    )
    def __crear_lista_vectores_velocidades(
        self, aerogeneradores: Dict, serie_tiempo: pd.DatetimeIndex
    ) -> List:
        """
        Crea una lista con vectores que representan las velocidades en base a la estampa del tiempo.
        
        Args:
            - aerogeneradores (Dict): Diccionario que contiene la informacion de los aerogeneradores.
            - serie_tiempo (pd.DatetimeIndex): Serie con las estampas de tiempo.
        Retorna:
            - vectores_velocidades (List): Lista con vectores de valocidades.
        """
        vectores_velocidades = []

        for fecha in serie_tiempo:
            lista_vel = []
            for aero in aerogeneradores.values():
                lista_vel.append(aero.df.at[fecha, "VelocidadViento"])
            lista_vel = np.array(lista_vel)
            vectores_velocidades.append(lista_vel)

        return vectores_velocidades

    def __estructura_xarray_vectorizado(self, aerogeneradores, serie_tiempo) -> xr.Dataset:
        """
        Crea el Dataset XArray para el calculo vectorizado.
        
        Args:
            - aerogeneradores (Dict): Diccionario que contiene la informacion de los aerogeneradores.
            - serie_tiempo (pd.DatetimeIndex): Serie con las estampas de tiempo.
        Retorna:
            - ds (xr.Dataset): xarray Dataset con coords [turbina, tiempo].
        """
        ds = crear_estructura_xarray_vectorizado(aerogeneradores, serie_tiempo)
        return ds

    def __estructura_xarray_curvas(self, aerogeneradores) -> xr.Dataset:
        """
        Crea la estructura xarray para acceder a las curvas en base al aerogenerador.
        
        Args:
            - aerogeneradores (Dict): Diccionario que contiene la informacion de los aerogeneradores.
            - modelos (Dict): Diccionario con la informacion de los modelos.
        Retorna:
            - ds (xr.Dataset): xarray Dataset con coords [turbina, numero_curvas]
        """
        ds = crear_estructura_curvas_xarray(aerogeneradores)
        return ds

    @capturar_excepciones(
            MensajesEolica.Estado.POTENCIA.value,
            MensajesEolica.Error.POTENCIA.value,
            CalculoExcepcion
    )
    def __calculo_potencia_vectorizado(
        self,
        potencia_data_df,
        caracteristicas_df: pd.DataFrame,
        estructura_xarray: xr.Dataset,
        curvas_xarray: xr.Dataset,
        params_trans: ParametrosTransversales,
        promedio_ohm: float
    ) -> xr.Dataset:
        """
        Modifica la estructura_xarray y agrega la potencia por cada estampa de tiempo.
        
        Args:
            - caracteristicas_df (pd.DataFrame): Dataframe con las caracteristicas de los aerogeneradores.
            - estructura_xarray (xr.Dataset): Dataset con los datos para cada aerogenerador.
            - densidad (pd.DataFrame): DataFrame con la densidad del buje para cada aerogenerador.
            - curvas_xarray (xr.Dataset): Dataset de curvas del fabricante de cada aerogenerador.
            - n_turbinas (int): Numero de turbinas.
            - n_estampas (int): Numero de estampas de tiempo.
            - params_trans (ParametrosTransversales): Parametros transversales.
            - promedio_ohm (float): promedio de resistencia.
        Retorna:
            - ds (xr.Dataset): Estructura xarray modificada con potencia.
        """
        ds = potencia_vectorizado_udf(
            potencia_data_df,
            caracteristicas_df,
            estructura_xarray,
            curvas_xarray,
            params_trans,
            promedio_ohm
        )

        return ds

    def __crear_df_energia_planta(
        self, estructura_xarray: xr.Dataset, serie_tiempo: pd.DatetimeIndex
    ) -> pd.Series:
        """
        Crea la serie de energia producida por la planta para cada estampa de tiempo.

        Args:
            - estructura_xarray (xr.Dataset): Dataset con los datos para cada aerogenerador.
            - serie_tiempo (pd.DatetimeIndex): Estampas del tiempo del calculo.
        Retorna:
            - energia_planta (pd.Series): Serie de energia producida por la planta para cada estampa de tiempo.
        """
        energia_planta = pd.Series(estructura_xarray['potencia_parque'].values)
        energia_planta.index = serie_tiempo
        energia_planta.name = "energia_kWh"

        return energia_planta

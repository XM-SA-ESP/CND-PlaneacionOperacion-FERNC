import os
import polars as pl
import pandas as pd
import time

from typing import List, Dict
from pandas.core.frame import DataFrame as Pandas_Dataframe
from xm_solarlib.pvsystem import PVSystem
from XM_FERNC_API.dominio.servicio.azure_blob.cliente_azure import ClienteAzure
from XM_FERNC_API.infraestructura.models.respuesta import Respuesta, Resultado
from XM_FERNC_API.infraestructura.models.solar.parametros import (
    JsonModelSolar,
    ParametrosTransversales,
    ParametrosInversor,
    ParametrosModulo,
)

from XM_FERNC_API.utils.consumidor import ConsumirApiEstado
from XM_FERNC_API.utils.mensaje_constantes import MensajesSolar
from XM_FERNC_API.utils.manipulador_dataframe import ManipuladorDataframe
from XM_FERNC_API.utils.manipulador_excepciones import BaseExcepcion, CalculoExcepcion, ManipuladorExcepciones
from XM_FERNC_API.utils.solar.funciones_dni_dhi import CalculoDniDhi
from XM_FERNC_API.utils.solar.funciones_pvsystem import (
    crear_array,
    crear_montura_con_seguidores,
    crear_montura_no_seguidores,
)
from XM_FERNC_API.utils.solar.funciones_poa import poa_bifacial, poa_no_bifacial
from XM_FERNC_API.utils.solar.funciones_cec import (
    obtener_parametros_fit_cec_sam,
    obtener_parametros_circuito_eq,
)
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from XM_FERNC_API.utils.solar.calculos_polars import calculo_temp_panel
from XM_FERNC_API.utils.solar.funciones_solucion_cec import obtener_solucion_circuito_eq
from XM_FERNC_API.utils.solar.funciones_calculo_dc_ac import CalculoDCAC
from XM_FERNC_API.utils.generar_archivo_excel import GenerarArchivoExcel
from XM_FERNC_API.utils.decoradores import capturar_excepciones

from logging import INFO, getLogger, StreamHandler, Formatter
from azure.monitor.opentelemetry import configure_azure_monitor
from pyspark.sql import SparkSession



import time
def timer(start,end):
   hours, rem = divmod(end-start, 3600)
   minutes, seconds = divmod(rem, 60)
   return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)
from XM_FERNC_API.utils.databricks_logger import DbLogger, timer


class ServicioSolar:
    def __init__(self) -> None:
        self.manipulador_df = ManipuladorDataframe()
        self.calculo_dni_dhi = CalculoDniDhi()
        self.calculo_dc_ac = CalculoDCAC()
        self.cliente_azure = None
        self.generar_archivo = GenerarArchivoExcel(self.manipulador_df, 0)

        self.inversores_pvsystem = None
        self.inversores_resultados = None

        self.logger_info = DbLogger('info')

        


    def generar_dataframe(self, nombre_blob: str) -> pl.DataFrame:
        """
        Método para generar dataframe(estructura de datos bidimensional).
        Params:
            -nombre_blob: Nombre del archivo loclizado en el blob storage de Azure

        Retorna:
            df: Dataframe generado a partir del archivo de Azure.
        """        
        df = pd.read_parquet(os.environ['VOLUME'] + nombre_blob)
        spark = SparkSession.builder.getOrCreate()
        if 'PYTEST_CURRENT_TEST' not in os.environ:
            from pyspark.dbutils import DBUtils
            dbutils = DBUtils(spark)
            dbutils.fs.rm(os.environ['VOLUME'] + nombre_blob)
        return df

    def ejecutar_calculos(self, df: pl.DataFrame, params: JsonModelSolar):
        """
        Método principal que ejecuta los cálculos y arroja los resultados del proceso completo para plantas solares.
        A partir de los archivos de series y demás valores del objeto se obtiene los resultados esperados.

        Params:
            - df (pl.DataFrame): Dataframe de Polars con la serie de datos ingresada por el usuario.
            - params (JsonModelSolar): Modelo que representa el objeto completo requerido para calculos de las plantas solares generado por la aplicación.

        Retorna:
            resultado: Objeto de tipo Respuesta que contiene el resultado final de la EDA, la lista de valores de la ENFICC por cada periodo de la serie y el nombre del archivo
            subido al blob storage con todos los resultados por cada fila de las series cargadas según sea el caso.
        """
        
        self.logger_info.initialize_logger()

        df["Ghi"] = df["Ghi"].str.replace(",", ".")
        df["Ta"] = df["Ta"].str.replace(",", ".")
        params_trans = params.ParametrosTransversales
        params_trans.Ihf = params_trans.Ihf / 100
        ID_CONEXION = params.IdConexionWs
        cae_instancia = ConsumirApiEstado(
            proceso="EstadoCalculo", conexion_id=ID_CONEXION, pasos_totales=5
        )

        try:
            start_global = time.time()                        
            print(f"Nombre planta:{params.ParametrosTransversales.NombrePlanta}")
            cae_instancia.consumir_api_estado(MensajesSolar.Estado.DNI_DHI.value, True)
            
            print("DNI/DHI")
            
            start = time.time()                                                      
            series_dni_dhi = self.ejecutar_calculo_dni_dhi(df, params)
            df.index = series_dni_dhi.index
            series_dni_dhi = self.manipulador_df.filtrar_dataframe(series_dni_dhi)
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " DNI/DHI ", start)
            
            print("Calculo POA")
            start = time.time()                             
            cae_instancia.consumir_api_estado(MensajesSolar.Estado.POA.value, True)            
            self.inversores_pvsystem, self.inversores_resultados = (
                self.ejecutar_calculo_poa(series_dni_dhi, params)
            )            
            self.manipulador_df.restaurar_dataframe(df, self.inversores_resultados)            
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Calculo POA ", start)

            print("Calcular Temperatura Panel")
            start = time.time()                               
            self.ejecutar_calculo_temperatura_panel()                                                         
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Calcular Temperatura Panel ", start)
            
            print("Calcular CEC")
            start = time.time()                        
            cae_instancia.consumir_api_estado(MensajesSolar.Estado.CIRCUITO_EQUIVALENTE.value, True)
            self.ejecutar_calculo_parametros_cec()
            self.ejecutar_calculo_solucion_cec()            
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Calcular CEC ", start)    
            
            print("Calculo Energias")
            start = time.time()                        
            cae_instancia.consumir_api_estado(MensajesSolar.Estado.ENERGIA_DC_AC.value, True)            
            inv_dict = self.calculo_energias(params_trans)                                 
            self.logger_info.send_logg("Calculo Energias ", start)                  
            
            print("Ajuste de Energias")
            start = time.time()
            cae_instancia.consumir_api_estado(MensajesSolar.Estado.AJUSTANDO_ENERGIA.value, True)
            energia_planta = self.ajustar_energias(inv_dict, params_trans)
            energia_al_mes = self.manipulador_df.filtrar_por_mes(energia_planta)
            energia_diaria = self.manipulador_df.filtrar_por_dia(energia_al_mes)                             
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Ajuste de Energias ", start)                      

            
            print("Calculo ENFICC")
            start = time.time()                               
            resultado_enficc = self.calcular_enficc(params_trans, energia_diaria)                      
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Calculo ENFICC ", start)               
            
            print("Calculo EDA")
            start = time.time()                        
            resultado_eda = self.manipulador_df.calcular_eda(
                params_trans, energia_diaria, resultado_enficc
            )
            resultado_enficc.valor = round(resultado_enficc.valor)
            nombre_archivo_resultado = (
                os.path.splitext(params.ArchivoSeries.Nombre)[0] + "_resultado.xlsx"
            )                                           
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " Calculo EDA", start)
            
            print("Guardando Archivo")
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
            self.logger_info.send_logg(params.ParametrosTransversales.NombrePlanta + " TIEMPO TOTAL: ", start_global)
            return resultado

        except BaseExcepcion as e:
            return ManipuladorExcepciones(e.error, e.tarea, e.mensaje)

        except Exception as e:
            print(f"Error no controlado: {e}")

    @capturar_excepciones(
        MensajesSolar.Estado.AJUSTANDO_ENERGIA.value, 
        MensajesSolar.Error.CIRCUITO_EQUIVALENTE_PARAMETROS.value, 
        CalculoExcepcion
    )
    def calculo_energias(self, params_trans):
        inv_dict = {}

        for i, k1 in enumerate(self.inversores_pvsystem.keys()):
            lista_array = []
            params_inversor = self.inversores_resultados[
                f"Inversor {i + 1} Array 1 POA"
            ]["params_inv"].ParametrosInversor
            params_modulo = self.inversores_resultados[f"Inversor {i + 1} Array 1 POA"][
                "params_inv"
            ].ParametrosModulo

            for k2, j in self.inversores_resultados.items():
                if f"Inversor {i + 1} Array" in k2:
                    lista_array.append(j["solucion_cec"])

            pvsys = self.inversores_pvsystem[k1]            
            resultado = self.ejecutar_calculo_dc_ac(
                pvsys, lista_array, params_trans, params_inversor, params_modulo
            )

            inv_dict[f"Inversor {i + 1}"] = resultado

        return inv_dict

    @capturar_excepciones(
        "Calculando y ajustando energia",
        "Error en el calculo y ajuste de la energia AC",
        CalculoExcepcion
    )
    def ajustar_energias(self, inv_dict, params_trans):
        energia_planta = self.ejecutar_calculo_energia(inv_dict)
        energia_planta = self.calculo_dc_ac.ajuste_potencia_con_ihf_perdidas(
            energia_planta, params_trans
        )

        return energia_planta

    @capturar_excepciones(
        MensajesSolar.Estado.DNI_DHI.value, 
        MensajesSolar.Error.DNI_DHI.value, 
        CalculoExcepcion)
    def ejecutar_calculo_dni_dhi(self, df: pd.DataFrame, params: JsonModelSolar):
        """
        Método para generar dataframe(estructura de datos bidimensional).
        Params:
            -nombre_blob: Nombre del archivo loclizado en el blob storage de Azure

        Retorna:
            df: Dataframe generado a partir del archivo de Azure.
        """
        series_tiempo = self.manipulador_df.crear_serie_doy(
            df, params.ParametrosTransversales.ZonaHoraria
        )
        localizacion = self.calculo_dni_dhi.obtener_localizacion(
            params.ParametrosTransversales.Latitud,
            params.ParametrosTransversales.Longitud,
            params.ParametrosTransversales.ZonaHoraria,
            params.ParametrosTransversales.Altitud,
        )
        angulo_zenital = self.calculo_dni_dhi.obtener_angulo_zenital(
            localizacion, series_tiempo
        )
        irradiacion_extraterrestre = (
            self.calculo_dni_dhi.obtener_irradiacion_extraterrestre(series_tiempo)
        )
        calculo_df = self.manipulador_df.crear_df_calculo_dni(
            angulo_zenital, irradiacion_extraterrestre, df
        )
        series_dni = self.calculo_dni_dhi.obtener_dni(calculo_df)
        series_dni_dhi = self.calculo_dni_dhi.obtener_dhi(series_dni, calculo_df)

        series_dni_dhi = self.manipulador_df.combinar_dataframes(
            series_dni_dhi, angulo_zenital, irradiacion_extraterrestre
        )

        return series_dni_dhi

    @capturar_excepciones(
        MensajesSolar.Estado.POA.value, 
        MensajesSolar.Error.POA.value, 
        CalculoExcepcion)
    def ejecutar_calculo_poa(
        self, df_dni_dhi: Pandas_Dataframe, params: JsonModelSolar
    ):
        """
        Ejecuta el cálculo de la POA (Plane of Array) para un dataframe.

        Args:
            - df_dni_dhi (pd.DataFrame): El dataframe que contiene los valores de DNI y DHI.
            - params (JsonModelSolar): El objeto JSON que contiene los parámetros del modelo solar.

        Retorna:
            tuple: Una tupla que contiene dos diccionarios.
                - El primer diccionario (inversores_pvsystem) contiene objetos PVSystem para cada inversor.
                - El segundo diccionario (inversores_resultados) contiene los resultados de POA para cada combinación de inversor y arreglo.
        """
        inversores_pvsystem = {}
        inversores_resultados = {}
        params_trans = params.ParametrosTransversales

        for i, params_inv in enumerate(params.ParametrosConfiguracion.GrupoInversores):
            arrays = []

            for j, params_array in enumerate(
                params_inv.EstructuraYConfiguracion.CantidadPanelConectados
            ):
                if params_inv.EstructuraYConfiguracion.EstructuraPlantaConSeguidores:
                    montura = crear_montura_con_seguidores(params_array)
                else:
                    montura = crear_montura_no_seguidores(params_array)

                array = crear_array(montura, params_trans, params_array, nombre=f"Array {j + 1}")
                arrays.append(array)

                poa = self.calculo_poa(df_dni_dhi, montura, params_trans, params_inv, params_array)

                inversores_resultados[f"Inversor {i + 1} Array {j + 1} POA"] = {
                    "POA": poa,
                    "params_inv": params_inv,
                    "params_array": params_array,
                }

            inv_sys = PVSystem(arrays=arrays, name=f"PVSys Inv {i + 1}")
            inversores_pvsystem[f"Inversor {i + 1} PvSystem"] = inv_sys

        return inversores_pvsystem, inversores_resultados

    def ejecutar_calculo_temperatura_panel(self) -> None:
        """
        Ejecuta el cálculo de la temperatura del panel para cada subarray de cada inversor.

        Esta función itera sobre cada valor en `self.inversores_resultados` y realiza los siguientes pasos:
        1. Convierte los datos de "POA" en un Polars DataFrame llamado `local_df`.
        2. Obtiene el valor de `TNoct` del diccionario "params_inv".
        3. Agrega una nueva columna llamada "temp_panel" a `local_df` utilizando la función `calculo_temp_panel`.
        4. Actualiza la columna "temp_panel" en el DataFrame "POA" con los valores de `local_df`.
        5. Elimina el DataFrame `local_df`.

        Args:
            None

        Retorna:
            None
        """
        for data in self.inversores_resultados.values():
            local_df = pl.from_pandas(data["POA"])
            t_noct = data["params_inv"].ParametrosModulo.Tnoct
            local_df = local_df.with_columns(
                [
                    pl.struct(["poa", "Ta", t_noct])
                    .apply(lambda cols: calculo_temp_panel(list(cols.values())))
                    .alias("temp_panel")
                ]
            )

            data["POA"]["temp_panel"] = local_df["temp_panel"]
            del local_df


    @capturar_excepciones(
        MensajesSolar.Estado.CIRCUITO_EQUIVALENTE.value,
        MensajesSolar.Error.CIRCUITO_EQUIVALENTE_PARAMETROS.value,
        CalculoExcepcion
    )
    def ejecutar_calculo_parametros_cec(self) -> None:
        """
        Ejecuta el cálculo de los parámetros para el circuito equivalente (CEC).

        Esta función itera sobre los valores del diccionario 'inversores_resultados' y realiza los siguientes pasos para cada dato:
        1. Obtiene los 'ParametrosModulo' del dataframe 'params_inv' del dato.
        2. Obtiene los parámetros para ajustar el CEC utilizando la función 'obtener_parametros_fit_cec_sam' y 'params_modulo'.
        3. Calcula los parámetros del circuito equivalente utilizando la función 'obtener_parametros_circuito_eq', 'POA', 'params_modulo' y 'params_cec_sam'.
        4. Transpone los parámetros calculados y asigna nombres de columna significativos al DataFrame resultante.
        5. Asigna los parámetros calculados a la clave 'params_cec' del dato.

        Args:
            None

        Retorna:
            None
        """        

        for data in self.inversores_resultados.values():
            params_modulo = data["params_inv"].ParametrosModulo
            params_cec_sam = obtener_parametros_fit_cec_sam(params_modulo)
            
            parametros_circuito_eq = obtener_parametros_circuito_eq(
                data["POA"], params_modulo, params_cec_sam
            )
            
            df_cec = pd.DataFrame(
                parametros_circuito_eq, 
                index=["photocurrent", "saturation_current", "resistance_series", "resistance_shunt", "nNsVth"]
            ).transpose()
            data["params_cec"] = df_cec


    @capturar_excepciones(
        MensajesSolar.Estado.CIRCUITO_EQUIVALENTE.value,
        MensajesSolar.Error.CIRCUITO_EQUIVALENTE_SOLUCION.value,
        CalculoExcepcion
    )
    def ejecutar_calculo_solucion_cec(self) -> None:
        """
        Ejecuta el cálculo de la solución para el circuito equivalente utilizando la funcion obtener_solucion_circuito_eq del
        modulo funciones_solucion_cec.

        Args:
            None

        Retorna:
            None
        """
        for data in self.inversores_resultados.values():
            solucion_cec = obtener_solucion_circuito_eq(data["params_cec"])

            df = pd.DataFrame(
                {
                    "i_sc": solucion_cec["i_sc"],
                    "v_oc": solucion_cec["v_oc"],
                    "i_mp": solucion_cec["i_mp"],
                    "v_mp": solucion_cec["v_mp"],
                    "p_mp": solucion_cec["p_mp"],
                    "i_x": solucion_cec["i_x"],
                    "i_xx": solucion_cec["i_xx"],
                }
            )
            df.index = data["POA"].index

            df.index = data["POA"].index
            data["solucion_cec"] = df


    def ejecutar_calculo_dc_ac(
        self,
        pvsys: PVSystem,
        lista_array: List,
        params_trans: ParametrosTransversales,
        params_inversor: ParametrosInversor,
        params_modulo: ParametrosModulo,
    ) -> pd.Series:
        """
        Ejecuta el cálculo de DC a AC.

        Args:
            - pvsys (PVSystem): El objeto del sistema fotovoltaico.
            - lista_array (List): La lista de arrays.
            - params_trans (ParametrosTransversales): Los parámetros transversales.
            - params_inversor (ParametrosInversor): Los parámetros del inversor.
            - params_modulo (ParametrosModulo): Los parámetros del módulo.

        Retorna:
            - resultado (pd.Series): El resultado del cálculo de DC a AC.
        """
        resultado = self.calculo_dc_ac.calculo_potencia_dc_ac(
            pvsys, lista_array, params_trans, params_inversor, params_modulo
        )

        return resultado

    def ejecutar_calculo_energia(self, inversores: Dict) -> pd.Series:
        """
        Calcula la energía total para un conjunto dado de inversores.

        Args:
            - inversores (Dict): Un diccionario que contiene DataFrames de mediciones de energía para cada inversor.

        Retorna:
            - resultado (pd.DataFrame): Un DataFrame que contiene el resultado del cálculo de energía total.
        """
        lista_series = []
        for df in inversores.values():
            lista_series.append(df)

        resultado = self.calculo_dc_ac.obtener_energia(lista_series)
        return resultado

    @capturar_excepciones(
        MensajesSolar.Estado.ENFICC.value,
        MensajesSolar.Error.ENFICC.value,
        CalculoExcepcion
    )
    def calcular_enficc(
        self, params_trans: ParametrosTransversales, energia_diaria_df
    ) -> Resultado:
        """
        Calcula el valor de enficc basado en los parámetros y los datos de energía proporcionados.

        Args:
            - params_trans (ParametrosTransversales): Los parámetros transversales.
            - energia_diaria_df (pd.DataFrame): Los datos de energía diaria.

        Retorna:
            - resultado (Resultado): El valor de enficc calculado.
        """
        valor_minimo_diario = energia_diaria_df["diaria"].min()
        fecha_minimo_diario = energia_diaria_df[
            energia_diaria_df["diaria"] == valor_minimo_diario
        ].index[0]
        energia_calculada = 12 * params_trans.Cen * (1 - params_trans.Ihf) * 1000

        energia_firme = min(valor_minimo_diario, energia_calculada)
        # En caso de que la planta NO cuente con información medida
        if not params_trans.InformacionMedida:
            energia_firme = valor_minimo_diario * 0.8

        resultado = Resultado(
            anio=int(fecha_minimo_diario.year),
            mes=int(fecha_minimo_diario.month),
            valor=energia_firme,
        )

        return resultado

    def generar_lista_meses(self, anio):
        """
        Genera una lista de meses para un año dado.

        Args:
            - anio (int): El año para el cual generar la lista de meses.

        Retorna:
            - meses (List): Una lista de objetos Resultado que representan los meses del año dado.
        """
        meses = []
        meses.append(Resultado(anio - 1, 12, 0))

        for mes in range(1, 12):
            meses.append(Resultado(anio, mes, 0))

        return meses

    def generar_archivo_excel(
        self,
        energia_planta,
        energia_mes,
        energia_diaria,
        enficc: Resultado,
        eda: list[Resultado],
        nombre_archivo,
    ):
        """
        Genera un archivo de Excel con múltiples hojas y lo sube a Azure Blob Storage.

        Args:
            - energia_planta (DataFrame): Datos de energía de la planta.
            - energia_mes (DataFrame): Datos de energía mensual.
            - energia_diaria (DataFrame): Datos de energía diaria.
            - enficc (Resultado): Datos de ENFICC.
            - eda (list[Resultado]): Lista de resultados de EDA.
            - nombre_archivo (str): Nombre del archivo Excel.

        Retorna:
            None
        """
        energia_planta = self.manipulador_df.transform_energia_planta(energia_planta)
        energia_mes = self.manipulador_df.transform_energia_mes(energia_mes)
        energia_diaria = self.manipulador_df.transform_energia_diaria(energia_diaria)
        df_enficc = self.manipulador_df.transform_enficc(enficc)
        df_eda = self.manipulador_df.transform_eda(eda)
        # Crear un diccionario donde cada clave es el nombre de una hoja,
        # y cada valor es un DataFrame o Serie que quieres escribir en esa hoja

        diccionario_hojas = {
            "E_Horaria": energia_planta,
            "E_Mensual": energia_mes,
            "Em": energia_diaria,
            "ENFICC": df_enficc,
            "EDA": df_eda,
        }

        # Llamar a la función generar_archivo_excel_y_subir para escribir los DataFrames
        # en el archivo Excel y subirlo a Azure Blob Storage
        self.cliente_azure.generar_archivo_excel_y_subir(
            diccionario_hojas, nombre_archivo
        )
    
    def calculo_poa(
        self,
        df_dni_dhi: pd.DataFrame,
        montura,
        params_trans,
        params_inv,
        params_array,
    ):
        """
        Calcula la irradiancia del plano del arreglo (POA) basado en los parámetros proporcionados.

        Parámetros:
            df_dni_dhi (pd.DataFrame): Un DataFrame que contiene los datos de irradiación directa normal (DNI) e irradiación difusa horizontal (DHI).
            montura (FixedMount | SingleAxisTrackerMount): Objeto xm_solarlib con la configuración de montaje de los paneles solares.
            params_trans: Los parámetros transversales del sistema.
            params_inv: Los parámetros del inversor.
            params_array: Los parámetros del arreglo de paneles solares.

        Retorna:
            poa (pd.DataFrame): Un Pandas DataFrame con los datos de la POA.

        """
        montura = montura.get_orientation(
            solar_azimuth=df_dni_dhi.azimuth,
            solar_zenith=df_dni_dhi.zenith,
        )
        if params_inv.ParametrosModulo.Bifacial:
            poa = poa_bifacial(
                df_dni_dhi, montura, params_trans, params_inv, params_array
            )

            return poa
        else:
            poa = poa_no_bifacial(df_dni_dhi, montura, params_trans)

            return poa
import os
import functools
import multiprocessing

import polars as pl
import pandas as pd
import numpy as np
import xarray as xr

from typing import Dict, List, Tuple

from infraestructura.models.eolica.parametros import (
    JsonModelEolica,
    ParametrosTransversales,
)
from infraestructura.models.respuesta import Respuesta, Resultado
from dominio.servicio.azure_blob.cliente_azure import ClienteAzure

from utils import workers
from utils.decoradores import capturar_excepciones
from utils.mensaje_constantes import MensajesEolica
from utils.consumidor import ConsumirApiEstado
from utils.estructura_xarray import (
    crear_estructura_xarray_vectorizado,
    crear_estructura_curvas_xarray
)
from utils.manipulador_excepciones import BaseExcepcion, CalculoExcepcion, ManipuladorExcepciones
from utils.manipulador_dataframe import ManipuladorDataframe
from utils.manipulador_modelos import ManipuladorModelos
from utils.eolica.manipulador_estructura import ManipuladorEstructura
from utils.eolica.funciones_calculo_temp_presion_densidad import (
    CalculoTempPresionDensidad,
)
from utils.eolica.funciones_corregir_curvas import CorregirCurvas
from utils.eolica.funciones_calculo_pcc import CalculoPcc
from utils.eolica.funciones_ordenamiento import Ordenamiento
from utils.eolica.funciones_correccion_velocidad_parque_eolico import (
    CorreccionVelocidadParque,
)
from utils.eolica.ajuste_potencia import potencia_vectorizado
from utils.eolica.dataclasses_eolica import Torre
from utils.generar_archivo_excel import GenerarArchivoExcel

import time

def timer(start,end):
   hours, rem = divmod(end-start, 3600)
   minutes, seconds = divmod(rem, 60)
   print("{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))


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
        self.generar_archivo = GenerarArchivoExcel(self.manipulador_df)

        self.cliente_azure = None

    def ejecutar_calculos(self, params: JsonModelEolica) -> Respuesta:
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
        POOL = None

        try:
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

                self.ajuste_curvas.corregir_curvas_sin_torres(params, df)

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
                aerogeneradores, len(serie_tiempo)
            )

            end = time.time()
            timer(start, end)

            lista_ordenamiento = []

            # Crear lista de ordenamientos por estampa
            for df in dict_ordenamiento.values():
                lista_ordenamiento.append(df["id_turbina"].to_list())

            h_buje_promedio = self.correccion_parques.calcular_h_buje_promedio(
                modelos, aerogeneradores
            )
            n_turbinas = len(aerogeneradores.keys())
            caracteristicas_df = self.__caracteristicas_tij(aerogeneradores, modelos)
            estructura_xarray = self.__estructura_xarray_vectorizado(
                aerogeneradores, serie_tiempo
            )

            args_list = self.__crear_lista_argumentos_correcciones(
                aerogeneradores,
                modelos,
                h_buje_promedio,
                offshore,
                z_o1,
                z_o2,
                serie_tiempo,
                lista_ordenamiento,
            )

            cantidad_cpu = os.cpu_count() - 1
            POOL = multiprocessing.Pool(processes=cantidad_cpu)
            print(f"os.cpu_count() {os.cpu_count()}")
            CHUNKS = self.__chunksize(n_workers=cantidad_cpu, len_iterable=len(serie_tiempo))
            print(f"CHUNKS:{CHUNKS}")

            print("Correccion parques")
            cae_instancia.consumir_api_estado(MensajesEolica.Estado.PARQUES.value, True)
            start = time.time()
            if offshore:

                for resultado in POOL.imap(
                    workers.correcciones_worker, args_list, chunksize=CHUNKS
                ):
                    self.__asignar_valores_aerogeneradores(
                        resultado, aerogeneradores, columna="VelocidadViento"
                    )
                vectores_velocidades = self.__crear_lista_vectores_velocidades(
                    aerogeneradores, serie_tiempo
                )
                estructura_xarray["velocidad_grandes_parques"] = (
                    ["turbina", "tiempo"],
                    np.array(vectores_velocidades).T,
                    {
                        "Descripción": "Velocidad del viento perturbada por efecto de grandes parques en [m/s]."
                    },
                )

            else:
                estructura_xarray["velocidad_grandes_parques"] = (
                    ["turbina", "tiempo"],
                    estructura_xarray["velocidad_viento"].values,
                    {
                        DESCRIPCION: "Velocidad del viento perturbada por efecto de grandes parques en [m/s]."
                    },
                )

            end = time.time()
            timer(start, end)

            print("Estela")
            cae_instancia.consumir_api_estado(MensajesEolica.Estado.ESTELA.value, True)
            start = time.time()
            densidad = pd.DataFrame(
                {key: value.df["DenBuje"] for key, value in aerogeneradores.items()}
            )
            curvas_xarray = self.__estructura_xarray_curvas(aerogeneradores)
            n_estampas = len(serie_tiempo)

            wrapper_estela = functools.partial(
                workers.wrapper_efecto_estela_vectorizado,
                offshore,
                cre,
                caracteristicas_df,
                densidad,
                estructura_xarray,
                n_turbinas,
                curvas_xarray,
            )

            velocidades_estela = POOL.map(
                wrapper_estela, ((i, dict_ordenamiento[list(dict_ordenamiento.keys())[i]]) for i in range(0, n_estampas)), chunksize=CHUNKS
            )

            estructura_xarray["velocidad_estela"] = (
                ["turbina", "tiempo"],
                np.array(velocidades_estela).T,
                {
                    DESCRIPCION: "Velocidad del viento perturbada por efecto estela en [m/s]."
                },
            )

            POOL.close()

            end = time.time()
            timer(start, end)

            print("Potencia")
            start = time.time()

            cae_instancia.consumir_api_estado(
                MensajesEolica.Estado.POTENCIA.value, True
            )
            estructura_xarray = self.__calculo_potencia_vectorizado(
                caracteristicas_df,
                estructura_xarray,
                densidad,
                curvas_xarray,
                n_turbinas,
                n_estampas,
                params_trans,
                promedio_ohm,
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

            end = time.time()
            timer(start, end)

            nombre_archivo_resultado = (
                os.path.splitext(self.cliente_azure.blob)[0] + "_resultado.xlsx"
            )

            energia_al_mes = self.manipulador_df.filtrar_por_mes(energia_planta)
            energia_diaria = self.manipulador_df.filtrar_por_dia(energia_al_mes)
            resultado_enficc = self.calcular_enficc(params_trans, energia_diaria)
            resultado_eda = self.manipulador_df.calcular_eda(
                params_trans, energia_diaria, resultado_enficc
            )

            resultado_enficc.valor = round(resultado_enficc.valor)

            self.generar_archivo.generar_archivo_excel(
                self.cliente_azure,
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

            return resultado
        except BaseExcepcion as e:
            if POOL:
                POOL.close()
                POOL.join()
                POOL.terminate()
            return ManipuladorExcepciones(e.error, e.tarea, e.mensaje)
        except Exception as e:
            if POOL:
                POOL.close()
                POOL.join()
                POOL.terminate()
            return ManipuladorExcepciones(e, "Ejecutando Calculos.", "Error no controlado.")

    def generar_dataframe(self, nombre_blob: str) -> pl.DataFrame:
        """
        Genera un dataframe usando el nombre del blob.
        Args:
            nombre_blob (str): Nombre del blob.
        Retorna:
            pl.DataFrame: El dataframe Polars generado.
        """
        self.cliente_azure = ClienteAzure(blob=nombre_blob)

        df = self.cliente_azure.archivo_leer()
        self.cliente_azure.archivo_blob_borrar()

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
            z_o2 = 0.03
            z_o1 = 0.0002
            cre = 0.04
        else:
            z_o2 = 0.05
            z_o1 = 0.055
            cre = 0.075
        return z_o1, z_o2, cre

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
        aerogeneradores: Dict,
        modelos: Dict,
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
                fecha,
                ordenamiento,
                aerogeneradores,
                modelos,
                h_buje_promedio,
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
        self, resultados: Tuple, aerogeneradores: Dict, columna: str
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
        fecha, velocidades = resultados[0], resultados[1]
        if len(velocidades) > 0:
            for aero_id, v in velocidades:
                aerogeneradores[aero_id].df.at[fecha, columna] = v

    def __chunksize(self, n_workers, len_iterable):
        """
        Calcula el parámetro 'chunksize' para los métodos multiprocessing.Pool().
        Se asemeja al código fuente dentro de 'multiprocessing.pool.Pool._map_async'.

        ref: https://stackoverflow.com/questions/53751050/multiprocessing-understanding-logic-behind-chunksize
        """
        chunksize, extra = divmod(len_iterable, n_workers)

        if extra:
            chunksize += 1

        return chunksize

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
        num_aeros = len(index)
        elevacion = [modelos[aero.modelo].altura_buje for aero in aerogeneradores.values()]
        diametro = [modelos[aero.modelo].diametro_rotor for aero in aerogeneradores.values()]
        densidad = [modelos[aero.modelo].den_nominal for aero in aerogeneradores.values()]
        distancia_pcc = [aero.dist_pcc for aero in aerogeneradores.values()]
        t_minima = [modelos[aero.modelo].t_min for aero in aerogeneradores.values()]
        t_maxima =[modelos[aero.modelo].t_max for aero in aerogeneradores.values()]
        p_nominal = [modelos[aero.modelo].p_nominal for aero in aerogeneradores.values()]
        radio = np.array(diametro) / 2
        area_rotor = np.pi * (radio**2)

        caracteristicas_df = pd.DataFrame({
            "altura_buje": np.full(num_aeros, elevacion),
            "radio": np.full(num_aeros, radio),
            "densidad": np.full(num_aeros, densidad),
            "area_rotor": np.full(num_aeros, area_rotor),
            "dist_pcc": np.full(num_aeros, distancia_pcc),
            "t_min": np.full(num_aeros, t_minima),
            "t_max": np.full(num_aeros, t_maxima),
            "p_nominal": np.full(num_aeros, p_nominal),
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
        caracteristicas_df: pd.DataFrame,
        estructura_xarray: xr.Dataset,
        densidad: pd.DataFrame,
        curvas_xarray: xr.Dataset,
        n_turbinas: int,
        n_estampas: int,
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
        ds = potencia_vectorizado(
            caracteristicas_df, estructura_xarray, densidad, curvas_xarray, n_turbinas, n_estampas, params_trans, promedio_ohm
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

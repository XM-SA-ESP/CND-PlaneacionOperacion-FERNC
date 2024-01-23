import polars as pl
import pandas as pd
import numpy as np

from multiprocessing import Pool

from typing import Dict, List


from infraestructura.models.eolica.parametros import (
    JsonModelEolica,
    ParametrosTransversales,
)
from infraestructura.models.respuesta import Respuesta, Resultado
from dominio.servicio.azure_blob.cliente_azure import ClienteAzure
from infraestructura.models.respuesta import Respuesta, Resultado

from utils.manipulador_dataframe import ManipuladorDataframe
from utils.manipulador_modelos import ManipuladorModelos
from utils.eolica.manipulador_estructura import ManipuladorEstructura
from utils.eolica.funciones_calculo_temp_presion_densidad import (
    CalculoTempPresionDensidad,
)
from utils.eolica.funciones_calculo_potencia import CalculoPotencia
from utils.eolica.funciones_corregir_curvas import CorregirCurvas
from utils.eolica.funciones_calculo_pcc import CalculoPcc
from utils.eolica.funciones_ordenamiento import Ordenamiento
from utils.eolica.funciones_correccion_velocidad_parque_eolico import (
    CorreccionVelocidadParque,
)
from utils.eolica.funciones_ajuste_potencia import AjustePotencia
from utils.eolica.dataclasses_eolica import Torre
from utils.generar_archivo_excel import GenerarArchivoExcel
from utils import workers


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
        self.instancia_calculo_potencia = CalculoPotencia()
        self.ajuste_potencia = AjustePotencia()

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
            subido al blobl storage con todos los resultados por cada fila de las series cargadas según sea el caso.
        """
        params_trans = params.ParametrosTransversales
        offshore = params_trans.Offshore
        promedio_ohm = self.__obtener_promedio_resistencia(params)
        z_o1, z_o2, cre = self.__obtener_z_cre_values(offshore)
        
        if params_trans.InformacionMedida:
            params, torres = self.actualizar_aerogenerador_a_torre_cercana(params)

            modelos, aerogeneradores = self.manipulador_estructura.crear_dict_modelos_aerogeneradores(params)

            torres = self.ejecutar_calculo_temperatura_presion_densidad(
                modelos, aerogeneradores, torres
            )
            serie_tiempo = self.manipulador_df.obtener_serie_tiempo_eolica(torres=torres)

            self.ajuste_curvas.corregir_curvas_con_torre(
                torres, modelos, aerogeneradores
            )

            aerogeneradores = self.manipulador_estructura.agregar_pcc(params, aerogeneradores)
            aerogeneradores = self.calculo_pcc.calculo_pcc_aerogenerador(
                params, aerogeneradores
            )
            aerogeneradores = self.__asignar_df_aerogeneradores(
                aerogeneradores, torres
            )

        else:
            df = self.generar_dataframe(params.ArchivoSeries.Nombre)
            modelos, aerogeneradores = self.manipulador_estructura.crear_dict_modelos_aerogeneradores(params)

            diccionario_resultado = self.ejecutar_calculo_temperatura_presion_densidad(
                modelos, aerogeneradores, dataframe=df
            )
            df = diccionario_resultado["dataframe"]
            serie_tiempo = self.manipulador_df.obtener_serie_tiempo_eolica(df=df)

            self.ajuste_curvas.corregir_curvas_sin_torres(params, df)

            aerogeneradores = self.manipulador_estructura.agregar_pcc(params, aerogeneradores)
            aerogeneradores = self.calculo_pcc.calculo_pcc_aerogenerador(
                params, aerogeneradores
            )
            aerogeneradores = self.__asignar_df_aerogeneradores(
                aerogeneradores, df=df
            )

        print("Densidad Buje\n")
        print(aerogeneradores[1].df.head())

        print("\nOrdenamiento\n")
        lista_ordenamiento = self.__crear_lista_ordenamiento(
            aerogeneradores, serie_tiempo
        )
        h_buje_promedio = self.correccion_parques.calcular_h_buje_promedio(
            modelos, aerogeneradores
        )

        # Multiproceso Pool
        pool = Pool()
        args_list = self.__crear_lista_argumentos(
            aerogeneradores,
            modelos,
            h_buje_promedio,
            offshore,
            z_o1,
            z_o2,
            cre,
            serie_tiempo,
            lista_ordenamiento,
        )

        print("Iniciando Multiproceso")
        resultados = pool.map(workers.correcciones_worker, args_list)

        # Cerrar Pool
        pool.close()

        for fecha, velocidades in resultados:
            for aero_id, v in velocidades:
                aerogeneradores[aero_id].df.at[fecha, "VelocidadEstela"] = v

        print("\nPotencia Aerogeneradores")
        aerogeneradores = self.instancia_calculo_potencia.calcular_potencia_aerogeneradores(aerogeneradores, modelos)

        aerogeneradores = self.ajuste_potencia.ajuste_potencia_aerogeneradores(params_trans, aerogeneradores, modelos, promedio_ohm)

        energia_planta = self.instancia_calculo_potencia.potencia_planta_eolica(aerogeneradores, params)

        nombre_archivo_resultado = self.cliente_azure.blob.split(".")[0] + "_resultado.xlsx"

        energia_al_mes = self.manipulador_df.filtrar_por_mes(energia_planta)

        energia_diaria = self.manipulador_df.filtrar_por_dia(energia_al_mes)

        resultado_enficc = self.calcular_enficc(params_trans, energia_diaria)

        resultado_eda = self.manipulador_df.calcular_eda(params_trans, energia_diaria, resultado_enficc)

        resultado_enficc.Valor = round(resultado_enficc.Valor)

        self.generar_archivo.generar_archivo_excel(
            self.cliente_azure,
            energia_planta=energia_planta,
            energia_mes=energia_al_mes,
            energia_diaria=energia_diaria,
            enficc=resultado_enficc,
            eda=resultado_eda,
            nombre_archivo=nombre_archivo_resultado,
        )
        resultado = Respuesta(nombre_archivo_resultado, [resultado_enficc], resultado_eda)

        return resultado

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

        return df

    def actualizar_aerogenerador_a_torre_cercana(self, params: JsonModelEolica) -> tuple:
        """
        Genera un tuple que contiene los params actualizados apuntando a las torres correctasy 
        un diccionario que contiene la id de las torres como key y las especificaciones como value

        Args:
            params: Objeto que contiene la informacion del JSON

        Retorna:
            tuple:
                - params (JsonModelEolica): Objeto actualizado con torres actualizadas.
                - torres (Dict): Diccionario con las informacion de las torres.
        """
        torres = self.crear_dict_torres(params)
        self.manipulador_modelos.ajustar_aerogeneradores(params, torres)

        return params, torres

    def ejecutar_calculo_temperatura_presion_densidad(
        self,
        modelos: Dict,
        aerogeneradores: Dict,
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
                modelos, aerogeneradores, torres, dataframe
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

    def __crear_lista_ordenamiento(
        self, aerogeneradores: Dict, serie_tiempo: pd.DatetimeIndex
    ) -> List:
        """
        Método para crear ordenamiento de los sistemas de medición respecto a los aerogeneradores, en caso tal y no tengo información
        se hace con respecto al datafrae que llega como parámetro.
        Params:
            -aerogeneradores: Diccionario de datos con los aerogeneradores configurados desde aplicación
            -torres: Diccionario de datos con las torres configuradas en los sistemas de medición
            -df: Dataframe de datos de archivos de series cuando no se tiene información medida
            
        Retorna:
            lista_ordenamiento: Lista ordenada de resultados.
        """
        (
            aerogeneradores,
            combinaciones_aero,
        ) = self.ordenamiento.crear_combinaciones_aeros(aerogeneradores)
        lista_ordenamiento = []
        for fecha in serie_tiempo:
            for resultado in self.ordenamiento.obtener_ordenamiento(
                aerogeneradores,
                combinaciones_aero,
                fecha,
            ):
                lista_ordenamiento.append(resultado)

        return lista_ordenamiento

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
            Anio=int(fecha_minimo_diario.year),
            Mes=int(fecha_minimo_diario.month),
            Valor=energia_firme,
        )
        return resultado

    def __crear_lista_argumentos(
        self,
        aerogeneradores: Dict,
        modelos: Dict,
        h_buje_promedio: np.float64,
        offshore: bool,
        z_o1: float,
        z_o2: float,
        cre: float,
        serie_tiempo: pd.DatetimeIndex,
        lista_ordenamiento: List,
    ):
        """
        Genera una lista de argumentos que seran consumidos por el worker en el multiproceso

        Args:
            - aerogeneradores (Dict): Diccionario que contiene la informacion de los aerogeneradores.
            - modelos (Dict): Diccionario que contiene la informacion de los modelos.
            - h_buje_promedio (float): Altura buje promedio.
            - offshore (bool): Parametro offshore del JSON.
            - z_o1 (float): Rugosidad del terreno.
            - z_o2 (float): Rugosidad aumentada por el parque.
            - cre (float): Constante que depende de offshore.
            - df (pd.Dataframe): Df que contiene la serie de datos.
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
                cre,
            )
            for fecha, ordenamiento in zip(serie_tiempo, lista_ordenamiento)
        ]
        return args_list
    
    def __obtener_promedio_resistencia(self, params: JsonModelEolica) -> np.float64:
        """
        Genera un promedio de la resistencia de los cableados que sera usado
        en el calculo de portencia

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

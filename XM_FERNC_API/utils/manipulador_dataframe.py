import pandas as pd
import polars as pl
from dataclasses import asdict
from typing import List, Dict
from pandas.core.frame import DataFrame as Pandas_Dataframe

from infraestructura.models.respuesta import Resultado
from infraestructura.models.solar.parametros import ParametrosTransversales as ParametrosTransversalesSolar
from infraestructura.models.solar.parametros import ParametrosTransversales as ParametrosTransversalesEolica

from utils import utils_data_constants

class ManipuladorDataframe:
    def __init__(self) -> None:
        return

    def crear_df_calculo_dni(
        self, solpos: Pandas_Dataframe, iext: Pandas_Dataframe, df: Pandas_Dataframe
    ):
        """
        Crea un nuevo DataFrame para el calculo de DNI.

        Args:
            - solpos (pd.DataFrame): Un DataFrame que contiene datos de posicion solar.
            - iext (pd.DataFrame): Un DataFrame que contiene datos de irradiacion extraterrestre.
            - df (pd.DataFrame): El DataFrame original.

        Retorna:
            - calculo_df (pd.DataFrame): Un nuevo DataFrame con los valores calculados.
        """
        ghi = df["Ghi"].astype(float)
        ghi = ghi * 1000
        calculo_df = pd.DataFrame(solpos.zenith)
        calculo_df["Iext"] = iext

        ghi.index = calculo_df.index
        calculo_df["GHI"] = ghi

        calculo_df["apparent_zenith"] = solpos.apparent_zenith
        return calculo_df

    def combinar_dataframes(
        self,
        series_dni_dhi: Pandas_Dataframe,
        solpos: Pandas_Dataframe,
        iext: Pandas_Dataframe,
    ) -> Pandas_Dataframe:
        """
        Combina los dataframes proporcionados para crear un nuevo dataframe con las columnas
        necesarias para los calculos.

        Args:
            - series_dni_dhi (pd.DataFrame): El dataframe que contiene los datos de DNI y DHI.
            - solpos (pd.DataFrame): El dataframe que contiene los datos de la posicion solar (zenith, apparent_zenith, etc.).
            - iext (pd.DataFrame): El dataframe que contiene los datos de irradiacion extraterrestre.

        Retorna:
            - df (pd.Dataframe): El dataframe combinado.
        """
        df = series_dni_dhi.copy()
        df.loc[:, "azimuth"] = solpos["azimuth"]
        df.loc[:, "iext"] = iext
        df.loc[:, "apparent_zenith"] = solpos["apparent_zenith"]

        df = df.astype("float")

        return df

    def crear_serie_doy(self, df: Pandas_Dataframe, tz: str = "UTC") -> pd.DatetimeIndex:
        """
        Combina las columnas año, mes, dia y hora para generar un indice de tipo pd.DatetimeIndex
        en formato %Y-%m-%d %H para usar en los calculos.

        Args:
            - df (pd.DataFrame): Dataframe original con los datos ingresados.
            - tz (str): Zona horaria (UTC por default)
        Retorna:
            - times (pd.DatimeIndex): DatetimeIndex en formato %Y-%m-%d %H.
        """
        times = pd.to_datetime(
            df["Ano"].astype(str)
            + "-"
            + df["Mes"].astype(str)
            + "-"
            + df["Dia"].astype(str)
            + " "
            + df["Hora"].astype(str),
            format="%Y-%m-%d %H",
        )

        times = pd.DatetimeIndex(pd.to_datetime(times)).tz_localize(tz)

        return times

    def filtrar_dataframe(self, df: Pandas_Dataframe) -> Pandas_Dataframe:
        """
        Filtra un dataframe de Pandas removiendo filas si estan cumplen algunas condiciones.

        Args:
            df (pd.DataFrame): El dataframe con los resultados DNI y DHI.

        Retorna:
            local_df (pd.DataFrame): El dataframe filtrado, con filas removidas si cumplen las siguientes condiciones:
                - Hora entre 6:00 y 18:00.
                - La columna 'dni' es igual a 0 y la columna 'dhi' es igual a 0.
                - Todos los valores en la fila son iguales a 0.
        """
        local_df = df.copy()
        local_df = local_df.between_time("6:00", "18:00")
        local_df.loc[(local_df["dni"] == 0) & (local_df["dhi"] == 0), :] = 0
        local_df = local_df.loc[~(local_df == 0).all(axis=1)]
        return local_df

    def restaurar_dataframe(self, series_df, inversores_df) -> None:
        """
        Restaura los dataframes dados realizando operaciones específicas.

        Args:
            - series_df (pd.DataFrame): El dataframe que contiene los datos de la serie.
            - inversores_df (pd.DataFrame): El dataframe que contiene los datos de los inversores.

        Retorna:
            None

        La función restaura los dataframes realizando las siguientes operaciones:
        - Crea un dataframe vacio llamado series_dummy.
        - Establece el índice de series_dummy para que coincida con el indice de series_df.
        - Asigna el valor 0.0 a la columna "poa" de series_dummy.
        - Recorre los valores de inversores_df.
        - Suma la columna "POA" de series_dummy a la columna "POA" correspondiente en los datos actuales.
        - Convierte la columna "Ta" de series_df a tipo float y la asigna a la columna "Ta" de los datos actuales.
        - Rellena los valores faltantes en la columna "POA" con 0.0.
        """
        series_dummy = pd.DataFrame()
        series_dummy.index = series_df.index
        series_dummy["poa"] = 0.0
        for data in inversores_df.values():
            data["POA"] = series_dummy.add(data["POA"])
            data["POA"]["Ta"] = series_df.Ta.astype(float)
            data["POA"] = data["POA"].fillna(0.0)

    def filtrar_por_mes(self, serie_energia: pd.Series) -> pd.Series:
        """
        Filtra la serie de energía dada por mes.

        Args:
            - serie_energia (pd.Series): La serie de energía a filtrar.

        Retorna:
            - energia_mes (pd.Series): La serie de energía filtrada, sumada por mes y redondeada a 2 decimales.
        """
        energia_al_mes = serie_energia.resample("1m").sum()
        energia_al_mes = energia_al_mes.round(2)
        return energia_al_mes

    def filtrar_por_dia(self, serie_energia: pd.Series) -> pd.DataFrame:
        """
        Calcula la energía equivalente diaria a partir de la energía mensual.

        Parámetros:
        - serie_energia: Series con fechas como índice y energía como valores.

        Devoluciones:
        Un DataFrame con las mismas fechas como índice y las columnas 'mensual' 
        y 'diaria' con la energía mensual y diaria equivalente, respectivamente.
        """
        # Asegurar que el índice esté en formato datetime
        serie_energia.index = pd.to_datetime(serie_energia.index, format="%Y-%m")

        # Calcular la cantidad de días en cada mes y la energía diaria
        dias_del_mes = serie_energia.index.days_in_month
        energia_diaria = (serie_energia / dias_del_mes).round(2)

        # Crear el DataFrame con las columnas 'mensual' y 'diaria'
        df_resultado = pd.DataFrame(
            {"mensual": serie_energia, "diaria": energia_diaria}
        )

        return df_resultado

    def calcular_eda(self, params_trans: ParametrosTransversalesSolar | ParametrosTransversalesEolica, df_em: pd.DataFrame, enficc: Resultado) -> List[Resultado]:
        """
        Calcula la EDA (Exceso Diario Promedio) para un conjunto dado de parametros y datos.

        Args:
            - params_trans (ParametrosTransversales): Los parametros transversales.
            - df_em (pd.DataFrame): El DataFrame de entrada que contiene los datos diarios.
            - enficc (Resultado): El resultado de la EDA.

        Retorna:
            - resultados (List[Resultado]): Una lista de objetos Resultado que contiene los valores de EDA calculados para cada mes.
        """
        
        df_em.index = pd.to_datetime(df_em.index).tz_convert(None).to_period('M')

        # Extraemos el año de ENFICC
        anio_enficc = enficc.anio

        # Definimos el rango de fechas que nos interesa: desde diciembre del año pasado hasta noviembre del año actual
        fecha_inicio = f"{anio_enficc-1}-12-01"
        fecha_fin = f"{anio_enficc}-11-30"  # Establecer el último día de noviembre

        # Crear un índice con todas las fechas deseadas
        rango_fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq="M").to_period('M')

        # Filtramos el dataframe para esas fechas y reindexamos para incluir fechas faltantes
        df_filtrado = df_em.loc[fecha_inicio:fecha_fin].reindex(rango_fechas)
        
        # Calculamos la EDA para cada mes usando la columna 'diaria'
        if params_trans.InformacionMedida:
            eda = df_filtrado["diaria"] - enficc.valor
        else:
            eda = pd.Series(0, index=rango_fechas)
        
        # Crear una lista de objetos Resultado
        resultados = [
            Resultado(anio=fecha.year, mes=fecha.month, valor= round(valor, 2) if not pd.isna(valor) else None)
            for fecha, valor in eda.items()
        ]        

        return resultados

    def ajustar_df_eolica(self, df: pl.DataFrame) -> pd.DataFrame:
        """
        Ajusta el DataFrame con la serie de datos para el calculo de la energia eolica.

        Args:
            df (pl.DataFrame): El DataFrame de polars a ajustar.

        Returns:
            - df (pd.DataFrame): El DataFrame ajustado con las siguientes columnas:
                - 'DireccionViento' (float): La direccion del viento.
                - 'PresionAtmosferica' (float): La presión atmosferica.
                - 'Ta' (float): La temperatura.
                - 'VelocidadViento' (float): La velocidad del viento.
        """
        df = df.to_pandas()
        series_tiempo = self.crear_serie_doy(df)
        df.index = series_tiempo
        df['DireccionViento'] = df['DireccionViento'].str.replace(',', '.')
        df['PresionAtmosferica'] = df['PresionAtmosferica'].str.replace(',', '.')
        df['VelocidadViento'] = df['VelocidadViento'].str.replace(',', '.')
        df['Ta'] = df['Ta'].str.replace(',', '.')
        df = df[["DireccionViento", "PresionAtmosferica", "Ta", "VelocidadViento"]]
        df = df.astype(float)        

        return df
    
    def obtener_serie_tiempo_eolica(
        self, df: pd.DataFrame=None, torres: Dict=None
    ) -> pd.DatetimeIndex:
        """
        Extrae el indice de tipo pd.DatetimeIndex del dataframe dependiendo si existen
        torres o si no existen torres.

        Args:
            - df (pd.DataFrame): Indice del tiempo en formato %Y-%m-%d %H (None por default).
            - torres (Dict): Diccionario con objetos Torre (None por default).
        Retorna:
            - serie_tiempo (pd.DatetimeIndex): Indice del tiempo en formato %Y-%m-%d %H.

        Nota: En caso de que no se cuente con informacion medida se usa el df directamente, si
        en caso contrario existen torres, se usa el diccionarion con los objetos Torre.
        """
        if torres:
            torre = next(iter(torres.values()))
            serie_tiempo = torre.dataframe.index
            return serie_tiempo
        
        serie_tiempo = df.index
        return serie_tiempo

    def transform_energia_planta(self, energia_planta: pd.Series) -> pd.DataFrame:
        """
        Transforma la Serie `energia_planta` en un DataFrame con columnas adicionales.

        Args:
            - energia_planta (pd.Series): La Serie de entrada que contiene los datos de energía de una planta.

        Retorna:
            - energia_planta (pd.DataFrame): El DataFrame transformado con columnas adicionales 
            que representan el año, mes, día, hora y energía.
        """
        energia_planta = energia_planta.reset_index()

        energia_planta['Año'] = energia_planta['index'].dt.year.astype(int)
        energia_planta['Mes'] = energia_planta['index'].dt.month.astype(int)
        energia_planta['Día'] = energia_planta['index'].dt.day.astype(int)
        energia_planta['Hora'] = energia_planta['index'].dt.hour.astype(int)
        energia_planta = energia_planta.drop(columns=['index'])
        energia_planta = energia_planta.rename(columns={'energia_kWh': 'Energía [Kwh]'})

        # Reorganiza las columnas
        orden_columnas = ['Año', 'Mes', 'Día', 'Hora', 'Energía [Kwh]']
        energia_planta = energia_planta[orden_columnas]
        
        return energia_planta

    def transform_energia_mes(self, energia_mes: pd.Series) -> pd.DataFrame:
        """
        Transforma la serie de pandas de entrada `energia_mes` en un DataFrame de pandas.

        Parámetros:
            energia_mes (pd.Series): La serie de pandas de entrada que contiene los datos de energia_mes.

        Retorna:
            energia_mes (pd.DataFrame): El DataFrame de pandas transformado con las siguientes columnas:
                          - 'Año': El año extraido de la columna 'index' de energia_mes.
                          - 'Mes': El mes extraido de la columna 'index' de energia_mes.
                          - 'Energía [Kwh/mes]': El valor de 'energia_kWh' de energia_mes, renombrado.

        """
        energia_mes = energia_mes.reset_index()

        energia_mes['Año'] = energia_mes['index'].dt.year.astype(int)
        energia_mes['Mes'] = energia_mes['index'].dt.month.astype(int)
        energia_mes = energia_mes.drop(columns=['index'])
        energia_mes = energia_mes.rename(columns={'energia_kWh': 'Energía [Kwh/mes]'})

        # Reorganiza las columnas
        orden_columnas = ['Año', 'Mes', 'Energía [Kwh/mes]']
        energia_mes = energia_mes[orden_columnas]

        return energia_mes

    def transform_energia_diaria(self, energia_diaria: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma el DataFrame `energia_diaria` proporcionado al restablecer el índice, 
        agregando las columnas 'Año' y 'Mes' basadas en los valores del año y el mes de 
        la columna 'index', respectivamente. Elimina las columnas 'index' y 'mensual'. Renombra la columna 'diaria' a 'Em [kWh/día]'. 
        Reorganiza las columnas en el DataFrame según el orden especificado en la lista 'orden_columnas'. 
        Retorna el DataFrame 'energia_diaria' transformado.
        
        Args:
            - energia_diaria (pd.DataFrame): El DataFrame de entrada que contiene los datos de energía diaria.
        
        Retorna:
            - energia_diaria (pd.DataFrame): El DataFrame 'energia_diaria' transformado con las columnas 'Año', 'Mes' y 'Em [kWh/día]'.
        """
        
        energia_diaria = energia_diaria.reset_index()

        energia_diaria['Año'] = energia_diaria['index'].dt.year.astype(int)
        energia_diaria['Mes'] = energia_diaria['index'].dt.month.astype(int)
        energia_diaria = energia_diaria.drop(columns=['index', 'mensual'])
        energia_diaria = energia_diaria.rename(columns={'diaria': 'Em [kWh/día]'})

        # Reorganiza las columnas
        orden_columnas = ['Año', 'Mes', 'Em [kWh/día]']
        energia_diaria = energia_diaria[orden_columnas]

        return energia_diaria

    def transform_enficc(self, enficc: Resultado) -> pd.DataFrame:
        """
        Transforma un objeto `Resultado` en un DataFrame de pandas.

        Args:
            - enficc (Resultado): El objeto `Resultado` a transformar.

        Retorna:
            - df_enficc (pd.DataFrame): El DataFrame transformado que contiene los datos de `Resultado`.
        """
        enficc_dict = asdict(enficc)
        df_enficc = pd.DataFrame([enficc_dict])
        df_enficc = df_enficc.rename(
            columns={"anio": "Año", "mes": "Mes", "valor": "ENFICC [kWh/día]"}
        )
        return df_enficc

    def transform_eda(self, eda: list[Resultado]) -> pd.DataFrame:
        """
        Transforma la lista dada de objetos Resultado en un DataFrame de Pandas.
        
        Args:
            eda (list[Resultado]): Una lista de objetos Resultado que representan datos de la EDA.
        
        Retorna:
            df_eda (pd.DataFrame): El DataFrame transformado que contiene los datos de la EDA.
        
        """
        lista_eda_dicts = [asdict(resultado) for resultado in eda]
        df_eda = pd.DataFrame(lista_eda_dicts)

        
        df_eda[['anio', 'mes']] = df_eda[['anio', 'mes']].astype({'anio': int, 'mes': int})
        df_eda = df_eda.rename(columns={
            'anio': 'Año',
            'mes': 'Mes',
            'valor': utils_data_constants.COLUMN_EDA
        })
        df_eda[utils_data_constants.COLUMN_EDA] = df_eda[utils_data_constants.COLUMN_EDA].fillna("N/A")
        return df_eda

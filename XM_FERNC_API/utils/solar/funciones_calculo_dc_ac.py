import math
import xm_solarlib
import pandas as pd
from typing import List
from xm_solarlib.pvsystem import PVSystem
from utils.decoradores import capturar_excepciones
from utils.manipulador_excepciones import CurvasExcepcion
from utils.mensaje_constantes import MensajesSolar
from infraestructura.models.solar.parametros import (
    ParametrosTransversales,
    ParametrosModulo,
    ParametrosInversor,
)


class CalculoDCAC:
    def __init__(self) -> None:
        return
    
    @capturar_excepciones(
        "Calculo de potencia DC/AC",
        MensajesSolar.Error.CURVAS.value,
        CurvasExcepcion
    )
    def calculo_potencia_dc_ac(
        self,
        pvsys: PVSystem,
        lista_array: List,
        params_trans: ParametrosTransversales,
        params_inversor: ParametrosInversor,
        params_modulo: ParametrosModulo
    ) -> pd.Series:
        """
        Calcula la potencia de salida de un sistema fotovoltaico desde la entrada de CC hasta la salida de CA.

        Parámetros:
        - pvsys (PVSystem): Instancia de la clase PVSystem que describe el sistema fotovoltaico.
        - lista_array (List): Lista de parámetros adicionales necesarios para el cálculo.
        - params_trans (ParametrosTransversales): Parámetros transversales del sistema fotovoltaico.
        - params_inversor (ParametrosInversor): Parámetros del inversor utilizado.
        - params_modulo (ParametrosModulo): Parámetros del módulo fotovoltaico utilizado.

        Retorno:
        - pd.Series: Serie que representa la potencia de salida en CA del sistema fotovoltaico.
        """
        energia_dc = self.calculo_potencia_dc(pvsys, lista_array, params_trans, params_modulo)
        energia_ac = self.calculo_potencia_ac(energia_dc, params_inversor)

        energia_ac = energia_ac * params_inversor.NInv

        return energia_ac

    def calculo_potencia_dc(
        self,
        pvsys: PVSystem,
        lista_array: List,
        params_trans: ParametrosTransversales,
        params_modulo: ParametrosModulo,
    ) -> List:
        """
        Calcula la potencia de salida en CC de un sistema fotovoltaico.

        Parámetros:
        - pvsys (PVSystem): Instancia de la clase PVSystem que describe el sistema fotovoltaico.
        - lista_array (List): Lista de parámetros adicionales necesarios para el cálculo.
        - params_trans (ParametrosTransversales): Parámetros transversales del sistema fotovoltaico.
        - params_modulo (ParametrosModulo): Parámetros del módulo fotovoltaico utilizado.

        Retorno:
        - List: Lista de DataFrames que representan la potencia de salida en CC para cada conjunto de parámetros.
        """
        psi = params_modulo.Psi
        resultado = pvsys.scale_voltage_current_power(tuple(lista_array), unwrap=False)
        lista_resultados = []
        for df in resultado:
            df = df[["i_mp", "v_mp", "p_mp"]].copy()
            energia_dc = self.ajuste_potencia_perdidas(df, psi, params_trans.L)
            lista_resultados.append(energia_dc)
        return lista_resultados

    def calculo_potencia_ac(
        self, lista_energia:List, params_inv: ParametrosInversor
    ) -> pd.Series:
        """
        Calcula la potencia de salida en AC de un sistema fotovoltaico utilizando un inversor.

        Parámetros:
        - lista_energia (List): Lista de DataFrames que representan la potencia de entrada en DC para diferentes condiciones.
        - params_inv (ParametrosInversor): Parámetros del inversor utilizado.

        Retorno:
        - pd.Series: Serie que representa la potencia de salida en AC del sistema fotovoltaico.
        """
        vdc_nominal = params_inv.VDCnominal
        voltaje_minimo = 9.93+0.874 * vdc_nominal
        voltaje_maximo = 66.45+1.123* vdc_nominal
        
        dc_voltage = [voltaje_minimo] * 7 + [vdc_nominal] * 7 + [voltaje_maximo] * 7
        dc_voltage_level = ['Vmin'] * 7 + ['Vnom'] * 7 + ['Vmax'] * 7
        
        data_curvas = pd.DataFrame({
            'dc_power': params_inv.PowerDc,
            'ac_power': params_inv.PowerAc,
            'dc_voltage': dc_voltage,
            'dc_voltage_level': dc_voltage_level
        })

        # Datos del inversor
        inverter_data = {
            "Paco": params_inv.PACnominal,
            "Pdco": params_inv.PDCnominal,
            "Vdco": params_inv.VDCnominal,
            "Pso": params_inv.PDCarranque,
            "Pnt": params_inv.PACnocturnoW
        }

        inverter_fit = xm_solarlib.inverter.fit_sandia(
                        ac_power=data_curvas['ac_power'],
                        dc_power=data_curvas['dc_power'],
                        dc_voltage=data_curvas['dc_voltage'],
                        dc_voltage_level=data_curvas['dc_voltage_level'],
                        p_ac_0=inverter_data["Paco"],
                        p_nt=inverter_data["Pnt"])
        
        if not self.son_curvas_validas(inverter_fit):
            raise CurvasExcepcion(
                error="Las curvas no estan definidas o no son validas.",
                tarea="Calculando Curvas",
                mensaje=MensajesSolar.Error.CURVAS.value,
            )
        
        # Combinar datos del inversor con datos de entrada
        inv_dict = {**inverter_fit, **inverter_data}
        
        v_dc = tuple([dc_df.loc[:, "v_mp"] for dc_df in lista_energia])
        p_dc = tuple([dc_df.loc[:, "p_mp"] for dc_df in lista_energia])

        resultado = xm_solarlib.inverter.sandia_multi(
            v_dc=v_dc,
            p_dc=p_dc,
            inverter=inv_dict
        )
        resultado.name = "p_ac"
        resultado.loc[resultado < 0] = 0

        return resultado
    
    def son_curvas_validas(self, inverter_fit: dict[str, any]) -> bool:
        """
        Verifica si todas las curvas necesarias en el ajuste del inversor son válidas.

        La función verifica si las propiedades 'C0', 'C1', 'C2' y 'C3' en el ajuste del inversor
        no son NaN (Not a Number).

        Params:
            inverter_fit (dict[str, any]): Un diccionario que contiene el ajuste del inversor,
                donde las claves son nombres de propiedades y los valores son los valores correspondientes
                a esas propiedades en el ajuste del inversor.

        Returns:
            bool: True si todas las curvas son válidas, False de lo contrario.
        """
        propiedades_a_verificar = ["C0", "C1", "C2", "C3"]
        return all(
            propiedad in inverter_fit and not math.isnan(inverter_fit[propiedad])
            for propiedad in propiedades_a_verificar
        )

    def ajuste_potencia_perdidas(
        self, df: pd.DataFrame, psi: float, l: float
    ) -> pd.DataFrame:
        """
        Ajusta la potencia de corriente máxima y la potencia máxima de un DataFrame para tener en cuenta las pérdidas.

        Parámetros:
        - df (pd.DataFrame): DataFrame que contiene las columnas 'i_mp' y 'p_mp' que se ajustarán.
        - psi (float): Porcentaje de pérdida por suciedad (de 0 a 100).
        - l (float): Porcentaje de pérdida por sombreado (de 0 a 100).

        Retorno:
        - pd.DataFrame: DataFrame ajustado con las pérdidas aplicadas a 'i_mp' y 'p_mp'.
        """
        df[["i_mp", "p_mp"]] = df[["i_mp", "p_mp"]].apply(
            lambda x: x * (1 - (psi / 100)) * (1 - (l / 100))
        )
        return df

    def ajuste_potencia_con_ihf_perdidas(
        self,
        series: pd.Series,
        params_trans: ParametrosTransversales,
    ) -> pd.Series:
        """
        Ajusta la potencia de una Serie teniendo en cuenta la pérdida de eficiencia por varios factores.

        Parámetros:
        - series (pd.Series): Serie que representa la potencia que se ajustará.
        - params_trans (ParametrosTransversales): Parámetros transversales para el ajuste de potencia.

        Retorno:
        - pd.Series: Serie ajustada con las pérdidas aplicadas.
        """
        ihf = params_trans.Ihf
        kpc = params_trans.Kpc
        kt = params_trans.Kt
        kin = params_trans.Kin

        series = series * (1 - (kpc / 100)) * (1 - (kt / 100)) * (1 - (kin / 100)) * (1 - ihf)

        # Limitar el valor máximo de la potencia total ajustada a Ppi para cada índice
        series = series.clip(upper=params_trans.Ppi)

        return series

    def obtener_energia(self, lista_series: List) -> pd.Series:
        """
        Obtiene la energía total a partir de una lista de series de potencia.

        Parámetros:
        - lista_series (List): Lista de series que representan la potencia en el tiempo.

        Retorno:
        - pd.Series: Serie que representa la energía total en kWh.
        """
        resultado = pd.concat(lista_series, axis=1, ignore_index=True)
        resultado = resultado.sum(axis=1)
        resultado = (resultado / 1000).round(2)  # Convercion Wh a kWh
        resultado.name = "energia_kWh"

        return resultado

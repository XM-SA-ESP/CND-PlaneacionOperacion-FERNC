import scipy
import pandas as pd
import numpy as np
import xarray as xr

from infraestructura.models.eolica.parametros import ParametrosTransversales


def potencia_vectorizado(
    caracteristicas_tij: pd.DataFrame,
    dataset: xr.Dataset,
    densidad: pd.DataFrame,
    curvas_xarray: xr.Dataset,
    n_turbinas: int,
    n_estampas: int,
    param_trans: ParametrosTransversales,
    ohm: float,
) -> xr.Dataset:
    """
    Calculo vectorizado de la potencia.

    Args:
        - caracteristicas_df (pd.DataFrame): Dataframe con las caracteristicas de los aerogeneradores.
        - dataset (xr.Dataset): Dataset con los datos para cada aerogenerador.
        - densidad (pd.DataFrame): DataFrame con la densidad del buje para cada aerogenerador.
        - curvas_xarray (xr.Dataset): Dataset de curvas del fabricante de cada aerogenerador.
        - n_turbinas (int): Numero de turbinas.
        - n_estampas (int): Numero de estampas de tiempo.
        - params_trans (ParametrosTransversales): Parametros transversales.
        - ohm (float): Promedio de resistencia.
    Retorna:
        - pot (xr.Dataset): Dataset que contiene la potencia producida por cada turbina para
        cada estampa de tiempo.
    """
    kpc = param_trans.Kpc
    kt = param_trans.Kt
    kin = param_trans.Kin
    voltaje = param_trans.Voltaje
    def _recorrer_estampas(n: int):
        # Velocidad estela
        temp_vel_ti = dataset['velocidad_estela'].T.values[n]

        # Interpolación spline cúbico
        def _spline_cubico(i):
            curvas = curvas_xarray.sel(turbina=i+1)
            cur_vel, cur_pot = curvas["cur_vel"].values, curvas["cur_pot"].values
            return float(scipy.interpolate.splev(x=temp_vel_ti[i], tck=scipy.interpolate.splrep(cur_vel, cur_pot, k=3)))

        pot = np.array(list(map(_spline_cubico, np.arange(stop=n_turbinas))))

        # Corrección temperatura operación
        pot = np.where(dataset['temperatura_ambiente'].T.values[n] < caracteristicas_tij['t_min'].values, 0, pot)
        pot = np.where(dataset['temperatura_ambiente'].T.values[n] > caracteristicas_tij['t_max'].values, 0, pot)

        # Corrección Cth instantánea
        pot = pot * caracteristicas_tij['densidad'].values / densidad.iloc[n].values

        # Pérdidas cableado
        pot = perdidas_cableado(
            voltaje=voltaje * 1000,
            resistencia=ohm,
            longitud_cable=caracteristicas_tij['dist_pcc'].values,
            potencia=pot
        )

        # Pérdidas frontera comercial
        pot = perdidas_frontera_comercial(
            potencia=pot,
            kpc=kpc,
            kt=kt,
            kin=kin
        )

        # Filtro potencia nominal
        pot = np.where(pot >= caracteristicas_tij['p_nominal'].values, caracteristicas_tij['p_nominal'].values, pot)

        return pot

    pot = np.array(list(map(_recorrer_estampas, np.arange(stop=n_estampas))))

    # Filtro valores negativos
    pot = np.where(pot < 0.0, 0.0, pot)

    # Velocidad con efecto estela en xr.Dataset
    dataset['potencia'] = (['turbina', 'tiempo'], pot.T, {'Descripción': 'Potencia AC de cada turbina en [kW].'})

    return dataset

def perdidas_cableado(
    voltaje: float, resistencia: float, longitud_cable: float, potencia: float
) -> float:
    """
    Calculo de las perdidas del cableado [kW]
    """
    return ((potencia * 1000) - ((((potencia * 1000)/voltaje)**2) * (resistencia * longitud_cable))) / 1000 # [kW]

def perdidas_frontera_comercial(
    potencia: float, kpc: float=0, kt: float=0, kin: float=0
) -> float:
    '''
    potencia entra en [kW] y sale en [kW]

    kpc : float
        Perdidas de transmision.
        Default = 0.0

    kt : float
        Perdidas asociadas con la transformacion.
        Default = 0.0

    kin : float
        Perdidas por interconexion.
        Default = 0.0

    '''
    return potencia * (1 - kpc / 100 - kt / 100 - kin / 100) # [kW]
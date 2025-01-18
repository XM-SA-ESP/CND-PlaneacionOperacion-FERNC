import numpy as np
import pandas as pd
import xarray as xr

from typing import Dict, Tuple

from XM_FERNC_API.utils.eolica.dataclasses_eolica import Aerogenerador
from XM_FERNC_API.utils.manipulador_excepciones import BaseExcepcion
from XM_FERNC_API.utils.mensaje_constantes import MensajesEolica

DESCRIPCION = 'Descripci�n'

def crear_estructura_xarray(
    serie_tiempo: pd.DatetimeIndex, aerogeneradores: Dict[int, Aerogenerador]
) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Crea dos estructuras xarray donde estaran guardadas las latitudes y longitudes en base al
    ordenamiento y a la fecha para cada aerogenerador.

    Args:
        - serie_tiempo (pd.DatetimeIndex): Serie de tiempo de los datos ingresados.
        - aerogeneradores (Dict): Diccionario que contiene objetos Aerogenerador.
    Retorna:
        - Tuple: Tupla que contiene:
            - lon_data (xr.DataArray): DataArray que contiene las longitudes para cada aerogenerador
            - lat_data (xr.DataArray): DataArray que contiene las latitudes para cada aerogenerador
    """
    lat_data = xr.DataArray(
        np.empty((len(serie_tiempo), len(aerogeneradores))),
        coords=[serie_tiempo, list(aerogeneradores.keys())],
        dims=["fecha", "aero_id"],
        name="lat_coords",
    )

    lon_data = xr.DataArray(
        np.empty((len(serie_tiempo), len(aerogeneradores))),
        coords=[serie_tiempo, list(aerogeneradores.keys())],
        dims=["fecha", "aero_id"],
        name="lon_coords",
    )

    # Llenar los valores de los DataArray con ceros.
    lat_data.values[:] = 0
    lon_data.values[:] = 0

    return lon_data, lat_data

def crear_estructura_xarray_vectorizado(aerogeneradores: Dict, serie_tiempo: pd.DatetimeIndex) -> xr.Dataset:
    ids_turbinas = list(aerogeneradores.keys())

    # Extract data arrays using list comprehensions and convert to numpy arrays
    velocs = np.array([aero.df["VelocidadViento"].to_numpy() for aero in aerogeneradores.values()])
    direcs = 90 - np.array([aero.df["DireccionViento"].to_numpy() for aero in aerogeneradores.values()])
    temps = np.array([aero.df["Ta"].to_numpy() for aero in aerogeneradores.values()])
    dens = np.array([aero.df["DenBuje"].to_numpy() for aero in aerogeneradores.values()])

    # Create the xarray Dataset
    ds = xr.Dataset(
        data_vars={
            'densidad': (['turbina', 'tiempo'], dens, {DESCRIPCION: 'Densidad a altura de cubo en [kg/m3].'}),
            'temperatura_ambiente': (['turbina', 'tiempo'], temps, {DESCRIPCION: 'Temperatura ambiente a altura de cubo en [°C].'}),
            'velocidad_viento': (['turbina', 'tiempo'], velocs, {DESCRIPCION: 'Velocidad del viento a altura de cubo en [m/s].'}),
            'direccion_viento': (['turbina', 'tiempo'], direcs, {DESCRIPCION: 'Dirección del viento a altura de cubo en [°].'}),
        },
        coords={
            'tiempo': (['tiempo'], serie_tiempo.astype(str).to_numpy(), {DESCRIPCION: 'Estampa temporal.'}),
            'turbina': (['turbina'], ids_turbinas, {DESCRIPCION: 'Numeración de turbinas.'}),
        }
    )
    
    if ds.to_array().isnull().any():
        raise ValueError("Error: El xarray contiene valores NaN.")

    return ds

def crear_estructura_curvas_xarray(aerogeneradores: Dict) -> xr.Dataset:
    """
    Estructura xarray para obtener las curvas del fabricante en base al id del aerogenerador.

    Args:
        - aerogeneradores (Dict): Diccionario que contiene objetos Aerogenerador.
        - modelos (Dict): Diccionario que contiene objetos Modelo.
    Retorna:
        - curvas_ds (xr.Dataset): XArray Dataset con las curvas para cada aerogenerador.
    """
    ids_turbinas = list(aerogeneradores.keys())

    cur_vel = np.vstack([np.array([data.SerieVcthCorregida for data in aero.curvas_fabricante]) for aero in aerogeneradores.values()])
    cur_pot = np.vstack([np.array([data.SeriePotencia for data in aero.curvas_fabricante]) for aero in aerogeneradores.values()])
    cur_coef = np.vstack([np.array([data.SerieCoeficiente for data in aero.curvas_fabricante]) for aero in aerogeneradores.values()])
    numero_curvas = cur_vel.shape[1]
    curvas_ds = xr.Dataset(
        data_vars={
            'cur_vel': (['turbina', 'numero_curvas'], cur_vel, {DESCRIPCION: 'Curvas velocidad.'}),
            'cur_pot': (['turbina', 'numero_curvas'], cur_pot, {DESCRIPCION: 'Curvas potencia.'}),
            'cur_coef': (['turbina', 'numero_curvas'], cur_coef, {DESCRIPCION: 'Curvas coeficiente.'}),
        },
        coords={
            'turbina': (['turbina'], ids_turbinas, {DESCRIPCION: 'Numeración de turbinas.'}),
            'numero_curvas': np.arange(numero_curvas),
        },
        attrs=None
    )

    return curvas_ds

import numpy as np
import pandas as pd
import xarray as xr

from typing import Dict, Tuple

from utils.eolica.dataclasses_eolica import Aerogenerador
from utils.manipulador_excepciones import BaseExcepcion
from utils.mensaje_constantes import MensajesEolica

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

    velocs = np.array([aero.df["VelocidadViento"].values for aero in aerogeneradores.values()])
    direcs = np.array([aero.df["DireccionViento"].values for aero in aerogeneradores.values()])
    temps = np.array([aero.df["Ta"].values for aero in aerogeneradores.values()])
    dens = np.array([aero.df["DenBuje"].values for aero in aerogeneradores.values()])

    direcs = 90 - direcs

    ds = xr.Dataset(
        data_vars={
            'densidad': (['turbina', 'tiempo'], dens, {DESCRIPCION: 'Densidad a altura de cubo en [kg/m3].'}),
            'temperatura_ambiente': (['turbina', 'tiempo'], temps, {DESCRIPCION: 'Temperatura ambiente a altura de cubo en [�C].'}),
            'velocidad_viento': (['turbina', 'tiempo'], velocs, {DESCRIPCION: 'Velocidad del viento a altura de cubo en [m/s].'}),
            'direccion_viento': (['turbina', 'tiempo'], direcs, {DESCRIPCION: 'Direcci�n del viento a altura de cubo en [�].'}),
        },
        coords={
            'tiempo': (['tiempo'], serie_tiempo, {DESCRIPCION: 'Estampa temporal.'}),
            'turbina': (['turbina'], ids_turbinas, {DESCRIPCION: 'Numeraci�n de turbinas.'}),
        },
        attrs=None
    )

    if np.isnan(ds).any():
        BaseExcepcion(
            "se han encontrado valores NaN.",
            "Creando estructura de xarray.",
            MensajesEolica.Error.XARRAY.value,
        )

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
    numero_aeros = len(ids_turbinas)

    cur_vel = np.vstack([np.array([data.SerieVcthCorregida for data in aero.curvas_fabricante]) for aero in aerogeneradores.values()])
    cur_pot = np.vstack([np.array([data.SeriePotencia for data in aero.curvas_fabricante]) for aero in aerogeneradores.values()])
    cur_coef = np.vstack([np.array([data.SerieCoeficiente for data in aero.curvas_fabricante]) for aero in aerogeneradores.values()])

    numero_curvas = len(cur_vel[0]) # Obtener el numero de curvas del fabricante
    
    # Reshape en arrays de dimenciones 50x25
    cur_vel = cur_vel.reshape(numero_aeros, numero_curvas)
    cur_pot = cur_pot.reshape(numero_aeros, numero_curvas)
    cur_coef = cur_coef.reshape(numero_aeros, numero_curvas)

    curvas_ds = xr.Dataset(
        data_vars={
            'cur_vel': (['turbina', 'numero_curvas'], cur_vel, {DESCRIPCION: 'Curvas velocidad.'}),
            'cur_pot': (['turbina', 'numero_curvas'], cur_pot, {DESCRIPCION: 'Curvas potencia.'}),
            'cur_coef': (['turbina', 'numero_curvas'], cur_coef, {DESCRIPCION: 'Curvas coeficiente.'}),
        },
        coords={
            'turbina': (['turbina'], ids_turbinas, {DESCRIPCION: 'Numeraci�n de turbinas.'}),
            'numero_curvas': np.arange(numero_curvas),
        },
        attrs=None
    )

    return curvas_ds

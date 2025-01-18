import xm_solarlib
import pandas as pd

from XM_FERNC_API.utils.solar import data_constants


def poa_bifacial(df_dni_dhi, montura, params_trans, params_inv, params_array):
    """
    Calcula la radiación incidente en el array fotovoltaico para un sistema bifacial.

    Parámetros:
    - df_dni_dhi: Un DataFrame que contiene datos de irradiancia directa normalizada (DNI) y difusa normalizada (DHI).
    - montura: Un objeto que representa la montura (con o sin seguidores) del sistema fotovoltaico.
    - params_trans: Un objeto que contiene parámetros transversales para el sistema fotovoltaico.
    - params_inv: Un objeto que contiene parámetros de inversores para el sistema fotovoltaico.
    - params_array: Un objeto que contiene parámetros relacionados con la configuración del array del sistema fotovoltaico.

    Retorno:
    - DataFrame: Un DataFrame que contiene la radiación incidente en el array fotovoltaico para el sistema bifacial.
    """    

    if params_inv.EstructuraYConfiguracion.EstructuraPlantaConSeguidores:
        axis_azimuth = params_array.OAzimutal
    else:
        axis_azimuth = params_array.OAzimutal + 90

    # Crear una instancia de la clase de datos PVFactorsParams
    params = xm_solarlib.bifacial.pvfactors.PvfactorsTimeseriesParams(
        solar_azimuth=df_dni_dhi.azimuth,
        solar_zenith=df_dni_dhi.apparent_zenith,
        surface_azimuth=montura["surface_azimuth"],
        surface_tilt=montura["surface_tilt"],
        axis_azimuth=axis_azimuth,
        timestamps=df_dni_dhi.index,
        dni=df_dni_dhi.dni,
        dhi=df_dni_dhi.dhi,
        gcr=(2.0 / 7.0),
        pvrow_height=params_inv.ParametrosModulo.AltoFilaPaneles,
        pvrow_width=params_inv.ParametrosModulo.AnchoFilaPaneles,
        albedo=params_trans.Albedo,
        n_pvrows=3,
        index_observed_pvrow=1,
        rho_front_pvrow=0.03,
        rho_back_pvrow=0.05,
        horizon_band_angle=15.0,
    )

    # Llama a la función pvfactors_timeseries con la instancia de la clase de datos
    poa = xm_solarlib.bifacial.pvfactors.pvfactors_timeseries(params)
    
    poa = pd.DataFrame(poa)
    poa = poa.transpose()
    poa["poa"] = poa["total_inc_front"] + (
        poa["total_inc_back"] * params_inv.ParametrosModulo.Bifacialidad
    )
    poa = poa[["poa"]]

    return poa


def poa_no_bifacial(df_dni_dhi, montura, params_trans):
    """
    Calcula la radiación incidente en el array fotovoltaico para un sistema no bifacial.

    Parámetros:
    - df_dni_dhi: Un DataFrame que contiene datos de irradiancia directa normalizada (DNI) y difusa normalizada (DHI).
    - montura: Un objeto que representa la montura (sin seguidores) del sistema fotovoltaico.
    - params_trans: Un objeto que contiene parámetros transversales para el sistema fotovoltaico.

    Retorno:
    - DataFrame: Un DataFrame que contiene la radiación incidente en el array fotovoltaico para el sistema no bifacial.
    """
    
    poa = xm_solarlib.irradiance.get_total_irradiance(
        surface_tilt=montura["surface_tilt"],
        surface_azimuth=montura["surface_azimuth"],
        solar_azimuth=df_dni_dhi.azimuth,
        solar_zenith=df_dni_dhi.zenith,
        dni=df_dni_dhi.dni,
        ghi=df_dni_dhi[data_constants.COLUMN_GHI],
        dhi=df_dni_dhi.dhi,
        dni_extra=df_dni_dhi.iext,
        airmass=df_dni_dhi.airmass,
        albedo=params_trans.Albedo,
        model="perez"
    )
    poa = poa[["poa_global"]]
    poa = poa.rename(columns={"poa_global": "poa"})

    return poa

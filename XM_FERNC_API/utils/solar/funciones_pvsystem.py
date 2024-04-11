import xm_solarlib


def crear_montura_con_seguidores(params_array):
    """
    Crea un objeto de montura con seguidores para un sistema fotovoltaico utilizando los parámetros proporcionados 
    y replicar el método SingleAxisTrackerMount de la librería xm_solarlib en un paquete privado de Python

    Parámetros:
    - params_array: Un objeto que contiene parámetros relacionados con la montura y seguidores del sistema fotovoltaico.

    Retorno:
    - SingleAxisTrackerMount: Un objeto que representa la montura con seguidores configurada según los parámetros proporcionados.
    """
    montura = xm_solarlib.pvsystem.SingleAxisTrackerMount(
        axis_tilt=params_array.OElevacion,
        axis_azimuth=params_array.OAzimutal,
        max_angle=params_array.OMax,
        backtrack=True,
        gcr=0.2857142857142857,
        cross_axis_tilt=0.0,
        racking_model=params_array.Racking.Value,
    )
    return montura


def crear_montura_no_seguidores(params_array):
    """
    Crea un objeto de montura sin seguidores para un sistema fotovoltaico utilizando los parámetros proporcionados.

    Parámetros:
    - params_array: Un objeto que contiene parámetros relacionados con la montura sin seguidores del sistema fotovoltaico.

    Retorno:
    - FixedMount: Un objeto que representa la montura sin seguidores configurada según los parámetros proporcionados.
    """
    montura = xm_solarlib.pvsystem.FixedMount(
        surface_azimuth=params_array.OAzimutal,
        surface_tilt=params_array.OElevacion,
        racking_model=params_array.Racking.Value,
    )
    return montura


def crear_array(montura, params_trans, params_array, nombre: str = None):
    """
    Crea un objeto Array para representar un sistema fotovoltaico utilizando los parámetros proporcionados.

    Parámetros:
    - montura: Un objeto que representa la montura (con o sin seguidores) del sistema fotovoltaico.
    - params_trans: Un objeto que contiene parámetros transversales para el sistema fotovoltaico.
    - params_array: Un objeto que contiene parámetros relacionados con la configuración del array del sistema fotovoltaico.
    - nombre (opcional): Un nombre para el array fotovoltaico.

    Retorno:
    - Array: Un objeto que representa el array fotovoltaico configurado según los parámetros proporcionados.
    """
    array = xm_solarlib.pvsystem.Array(
        name=nombre,
        mount=montura,
        albedo=params_trans.Albedo,
        module_type="glass_glass",
        modules_per_string=params_array.CantidadSerie,
        strings=params_array.CantidadParalero,
    )
    return array

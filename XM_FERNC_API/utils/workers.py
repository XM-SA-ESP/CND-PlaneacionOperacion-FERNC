from utils.eolica.funciones_correccion_velocidad_parque_eolico import (
    CorreccionVelocidadParque,
)
from utils.eolica.caracterizacion_estela import Estela


def correcciones_worker(args: tuple) -> tuple:
    """
    Worker para el multiproceso de la correccion de las velocidades.
    Args:
        args (tuple): Una tupla de argumentos que contiene:
            - fecha (pd.DatetimeIndex): Fecha de referencia.
            - ordenamiento (List): Lista de ordenamiento para fecha.
            - aerogeneradores_dict (Dict): El diccionario de aerogeneradores.
            - modelos (Dict): El diccionario de modelos.
            - h_buje_promedio (float): La altura promedio del buje.
            - offshore (boolean): Boolean que indica si el parametro offshore es True o False.
            - z_o1 (float): Rugosidad del terreno.
            - z_o2 (float): Rugosidad aumentada por el parque.
    Retorna:
        tuple: Una tupla que contiene:
            - fecha (pd.DatetimeIndex): La fecha.
            - velocidades (list): La lista de tuplas con id aero(int) y velocidades(float).
    """
    correccion_parques = CorreccionVelocidadParque()
    (
        fecha,
        ordenamiento,
        aerogeneradores_dict,
        modelos,
        h_buje_promedio,
        offshore,
        z_o1,
        z_o2,
    ) = args
    velocidades = []
    for v, aero_id in correccion_parques.correccion_velocidad_parque_eolico(
        fecha,
        ordenamiento,
        aerogeneradores_dict,
        modelos,
        h_buje_promedio,
        offshore,
        z_o1,
        z_o2,
    ):
        if v is not None:
            velocidades.append((aero_id, v))
    return fecha, velocidades

def wrapper_efecto_estela_vectorizado(offshore, cre, caracteristicas_tij, densidad, dataset, n_turbinas, curvas_xarray, n_estampa_df):

    estela = Estela(offshore=offshore,
                    cre=cre,
                    caracteristicas_tij=caracteristicas_tij,
                    densidad=densidad,
                    dataset=dataset,
                    n_turbinas=n_turbinas,
                    curvas_xarray=curvas_xarray,
                    n_estampa_df=n_estampa_df)

    return estela.efecto_estela_vectorizado()

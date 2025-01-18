import scipy
import numpy as np
import pandas as pd
import xarray as xr

from XM_FERNC_API.utils.decoradores import capturar_excepciones
from XM_FERNC_API.utils.manipulador_excepciones import BaseExcepcion, CalculoExcepcion
from XM_FERNC_API.utils.mensaje_constantes import MensajesEolica


def efecto_estela_vectorizado_refactor(
    offshore: bool,
    cre: float,
    densidad,
    turbine_info,
    estructura_info,
    n_turbinas: int,
    caracteristicas_df,
    curvas_info
) -> pd.Series:
    '''
    Estimación de velocidades perturbadas por efecto de estela
    ''' 
    txt_vel_dataset = 'velocidad_grandes_parques' if offshore else 'velocidad_viento'
    CONSTANTE_RADIO_ESTELA = cre
    wind_direction_rad = np.deg2rad(estructura_info['direccion_viento'])
    

    vecdir_tj = np.array([
        -np.cos(wind_direction_rad),  # [rad]
        -np.sin(wind_direction_rad),  # [rad]
        np.zeros(n_turbinas)  # [rad]
    ])

    # Velocidad del viento de las turbinas para la estampa n
    temp_vel_ti = estructura_info[txt_vel_dataset]

    # Cálculo del vector entre las turbinas t_i Y Tj
    longitudes = turbine_info['longitud_m']
    latitudes = turbine_info['latitud_m']
    elevations = turbine_info['Elevacion_m']
    heights = caracteristicas_df['altura_buje'].values
    radios = caracteristicas_df['radio'].values
    area_rotor = caracteristicas_df['area_rotor'].values
    densidades_turbine = caracteristicas_df['densidad'].values

    def _vector_tij(t_i):
        return np.array([
            longitudes[t_i] - longitudes,
            latitudes[t_i] - latitudes,
            (elevations[t_i] + heights[t_i]) - (elevations + heights)
        ])
    
    vecdirtur = [_vector_tij(t_i) for t_i in range(0, n_turbinas)]      
    proyec = np.sum(vecdirtur * vecdir_tj, axis=1)
    proyec = np.clip(proyec, 0, None)
    # Se determina si la estela de t_i va en dirección a Tj
    rectificador = (proyec > 0).astype(int)
    # Cálculo del radio de la estela Tj a la altura de t_i
    radio_estela = np.where(
            proyec > 0,
            radios + CONSTANTE_RADIO_ESTELA * proyec,
            0,
        )
    
    if np.isnan(radio_estela).any():
        raise ValueError("Error en estela en np.isnan")

    
    def _spline_cubico(cur_vel, cur_coef, temp_vel):
        return scipy.interpolate.splev(x=temp_vel, tck=scipy.interpolate.splrep(cur_vel, cur_coef, k=3))

    try:
        aux_ct = np.array([_spline_cubico(curvas_info['cur_vel'][i],
                                            curvas_info['cur_coef'][i] , 
                                            temp_vel_ti[i]) for i in range(n_turbinas)])
    except Exception as e:
        raise ValueError(f"Error en estela en aux_ct: {e}")

    
    if np.isnan(aux_ct).any():
        raise ValueError("Error en estela en if np.isnan 2")
            
    cth = aux_ct * densidades_turbine / densidad

    estela_ji = temp_vel_ti * (1 - (1 - np.sqrt(1 - cth))*(caracteristicas_df['radio'][turbine_info['id_turbina']].values/radio_estela)**2)
    estela_ji[(estela_ji == -np.inf) | (estela_ji == np.inf)] = 0    

    # Cálculo del centro de la estela de Tj a la altura de t_i
    centro_ji = np.stack([
        (longitudes + proyec * vecdir_tj[0]) * rectificador,
        (latitudes + proyec * vecdir_tj[1]) * rectificador,
        (elevations + heights) * rectificador
    ], axis=-1)

    
    # Distancia entre el centro de la estela Tj y el centro del rotor de la turbina t_i

    def _norma_distancia_estela_rotor(i):
        longitud_diff = (longitudes[i] - centro_ji[i].T[0]) * rectificador[i]
        latitud_diff = (latitudes[i] - centro_ji[i].T[1]) * rectificador[i]
        elevacion_diff = (elevations[i] + heights - centro_ji[i].T[2]) * rectificador[i]

        resultado = np.linalg.norm(np.array([longitud_diff, latitud_diff, elevacion_diff]), axis=0)

        if np.isnan(resultado).any():
            raise ValueError("Error en estela en if np.isnan 3")
        return resultado


    d = np.array([_norma_distancia_estela_rotor(i) for i in range(n_turbinas)])


    # Cálculo del área de efecto de la estela de Tj sobre el rotor de la turbina t_i
        
    radio_turbina = np.repeat(radios[None,:], repeats=n_turbinas, axis=0)
    area_rotor = np.repeat(area_rotor[None,:], repeats=n_turbinas, axis=0)

    def _koch(radio_turbina, area_rotor, radio_estela, d):
        def area_influencia_estela_caso1():
            d1 = abs(((radio_turbina**2) - (radio_estela**2) + (d**2)) / (2*d))
            z = abs((radio_turbina**2) - (d1**2))**0.5

            return (radio_turbina**2) * np.arccos(d1/radio_turbina) + (radio_estela**2) * np.arccos((d-d1)/radio_estela) - (d*z)

        def area_influencia_estela_caso2():
            d1 = abs(((radio_turbina**2) - (radio_estela**2) + (d**2)) / (2*d))
            z = abs((radio_turbina**2) - (d1**2))**0.5

            return area_rotor - (radio_turbina**2) * np.arccos(d1/radio_turbina) + (radio_estela**2) * np.arccos((d-d1)/radio_estela) - (d*z)

        NUMPY_CONDITIONS = [d >= (radio_turbina + radio_estela),
                            (d >= radio_estela) & (d < (radio_turbina + radio_estela)),
                            (d + radio_turbina >= radio_estela) & (d > (((radio_estela**2)-(radio_turbina**2))**0.5)),
                            (d + radio_turbina >= radio_estela) & (d <= (((radio_estela**2)-(radio_turbina**2))**0.5))]

        NUMPY_CHOICES = [0,
                        area_influencia_estela_caso1(),
                        area_influencia_estela_caso1(),
                        area_influencia_estela_caso2()]

        resultado =  np.select(condlist=NUMPY_CONDITIONS, choicelist=NUMPY_CHOICES, default=area_rotor)
        return resultado


    ashad = np.array(list(map(lambda x, y, z, w: _koch(x, y, z, w), radio_turbina.flatten(), area_rotor.flatten(), radio_estela.flatten(), d.flatten()))).reshape(n_turbinas, n_turbinas)
    ashad[np.isnan(ashad)] = 0

    beta = ashad / area_rotor ###

    difference = estela_ji - temp_vel_ti ##estela_ji
    squared_difference = difference ** 2

    suma = np.sum(beta * squared_difference * rectificador, axis=1)       

    
    # Velocidad perturbada por efecto estela
    vel_perturbada = temp_vel_ti - np.sqrt(suma)
    vel_perturbada = np.where(np.isnan(vel_perturbada) == True, temp_vel_ti, vel_perturbada)

    # Filtro por velocidad negativa
    vel_perturbada = np.where(vel_perturbada < 0, 0, vel_perturbada)

    return pd.Series(vel_perturbada, index=turbine_info['id_turbina']).sort_index().values

class Estela:
    """
    Clase que contiene los metodos para la caracterizacion de la estela
    """

    @capturar_excepciones(
            MensajesEolica.Estado.ESTELA.value,
            MensajesEolica.Error.ESTELA.value,
            CalculoExcepcion
    )




    def efecto_estela_vectorizado(
        self,
        offshore: bool,
        cre: float,
        caracteristicas_tij: pd.DataFrame,
        densidad: pd.DataFrame,
        dataset: xr.Dataset,
        n_turbinas: int,
        curvas_xarray: xr.Dataset,
        n_estampa_df: tuple,
    ) -> xr.Dataset:
        '''
        Estimación de velocidades perturbadas por efecto de estela
        ''' 
        txt_vel_dataset = 'velocidad_grandes_parques' if offshore else 'velocidad_viento'
        CONSTANTE_RADIO_ESTELA = cre
        wind_direction_rad = np.deg2rad(dataset['direccion_viento'].values.T[n_estampa_df[0]])
        

        vecdir_tj = np.array([
            -np.cos(wind_direction_rad),  # [rad]
            -np.sin(wind_direction_rad),  # [rad]
            np.zeros(n_turbinas)  # [rad]
        ])

        # Velocidad del viento de las turbinas para la estampa n
        temp_vel_ti = dataset[txt_vel_dataset].T.values[n_estampa_df[0]]

        # Cálculo del vector entre las turbinas t_i Y Tj
        longitudes = n_estampa_df[1]['longitud_m'].values
        latitudes = n_estampa_df[1]['latitud_m'].values
        elevations = n_estampa_df[1]['Elevacion_m'].values
        heights = caracteristicas_tij['altura_buje'][n_estampa_df[1]['id_turbina']].values
        def _vector_tij(t_i):
            return np.array([
                longitudes[t_i] - longitudes,
                latitudes[t_i] - latitudes,
                (elevations[t_i] + heights[t_i]) - (elevations + heights)
            ])

        
        vecdirtur = [_vector_tij(t_i) for t_i in range(0, n_turbinas)]      
        proyec = np.sum(vecdirtur * vecdir_tj, axis=1)
        proyec = np.clip(proyec, 0, None)
        # Se determina si la estela de t_i va en dirección a Tj
        rectificador = (proyec > 0).astype(int)
        # Cálculo del radio de la estela Tj a la altura de t_i
        radio_estela = np.maximum(0, caracteristicas_tij["radio"].values + CONSTANTE_RADIO_ESTELA * proyec)
        
        if np.isnan(radio_estela).any():
            raise ValueError("Error en estela en np.isnan")

        
        def _spline_cubico(curvas, temp_vel):
            cur_vel, cur_coef = curvas["cur_vel"].values, curvas["cur_coef"].values
            return scipy.interpolate.splev(x=temp_vel, tck=scipy.interpolate.splrep(cur_vel, cur_coef, k=3))

        curvas_list = [curvas_xarray.sel(turbina=i+1) for i in range(n_turbinas)]

        try:
            aux_ct = np.array([_spline_cubico(curvas_list[i], temp_vel_ti[i]) for i in range(n_turbinas)])
        except Exception as e:
            raise ValueError(f"Error en estela en aux_ct: {e}")

        
        if np.isnan(aux_ct).any():
            raise ValueError("Error en estela en if np.isnan 2")
             
        cth = aux_ct * caracteristicas_tij['densidad'].values / densidad.iloc[n_estampa_df[0]].values

        
        
        radio_values = caracteristicas_tij['radio'][n_estampa_df[1]['id_turbina']].values
        altura_buje_values = caracteristicas_tij['altura_buje'][n_estampa_df[1]['id_turbina']].values
        longitud_m_values = n_estampa_df[1]['longitud_m'].values
        latitud_m_values = n_estampa_df[1]['latitud_m'].values
        elevacion_m_values = n_estampa_df[1]['Elevacion_m'].values

        # Velocidad de estela de Tj al llegar a t_i
        factor = (1 - np.sqrt(1 - cth)) * (radio_values / radio_estela)**2
        estela_ji = temp_vel_ti * (1 - factor)
        estela_ji[np.isinf(estela_ji)] = 0

        # Cálculo del centro de la estela de Tj a la altura de t_i
        centro_ji = np.stack([
            (longitud_m_values + proyec * vecdir_tj[0]) * rectificador,
            (latitud_m_values + proyec * vecdir_tj[1]) * rectificador,
            (elevacion_m_values + altura_buje_values) * rectificador
        ], axis=-1)

        
        # Distancia entre el centro de la estela Tj y el centro del rotor de la turbina t_i
        altura_buje_values = caracteristicas_tij['altura_buje'][n_estampa_df[1]['id_turbina']].values

        def _norma_distancia_estela_rotor(i):
            longitud_diff = (n_estampa_df[1]['longitud_m'][i+1] - centro_ji[i].T[0]) * rectificador[i]
            latitud_diff = (n_estampa_df[1]['latitud_m'][i+1] - centro_ji[i].T[1]) * rectificador[i]
            elevacion_diff = (n_estampa_df[1]['Elevacion_m'][i+1] + altura_buje_values - centro_ji[i].T[2]) * rectificador[i]

            resultado = np.linalg.norm(np.array([longitud_diff, latitud_diff, elevacion_diff]), axis=0)

            if np.isnan(resultado).any():
                raise ValueError("Error en estela en if np.isnan 3")
            return resultado


        d = np.array([_norma_distancia_estela_rotor(i) for i in range(n_turbinas)])


        # Cálculo del área de efecto de la estela de Tj sobre el rotor de la turbina t_i
          
        radio_turbina = np.repeat(caracteristicas_tij['radio'].values[None,:], repeats=n_turbinas, axis=0)
        area_rotor = np.repeat(caracteristicas_tij['area_rotor'].values[None,:], repeats=n_turbinas, axis=0)



        def _koch(radio_turbina, area_rotor, radio_estela, d):
            def area_influencia_estela_caso1():
                d1 = abs(((radio_turbina**2) - (radio_estela**2) + (d**2)) / (2*d))
                z = abs((radio_turbina**2) - (d1**2))**0.5

                return (radio_turbina**2) * np.arccos(d1/radio_turbina) + (radio_estela**2) * np.arccos((d-d1)/radio_estela) - (d*z)

            def area_influencia_estela_caso2():
                d1 = abs(((radio_turbina**2) - (radio_estela**2) + (d**2)) / (2*d))
                z = abs((radio_turbina**2) - (d1**2))**0.5

                return area_rotor - (radio_turbina**2) * np.arccos(d1/radio_turbina) + (radio_estela**2) * np.arccos((d-d1)/radio_estela) - (d*z)

            NUMPY_CONDITIONS = [d >= (radio_turbina + radio_estela),
                                (d >= radio_estela) & (d < (radio_turbina + radio_estela)),
                                (d + radio_turbina >= radio_estela) & (d > (((radio_estela**2)-(radio_turbina**2))**0.5)),
                                (d + radio_turbina >= radio_estela) & (d <= (((radio_estela**2)-(radio_turbina**2))**0.5))]

            NUMPY_CHOICES = [0,
                            area_influencia_estela_caso1(),
                            area_influencia_estela_caso1(),
                            area_influencia_estela_caso2()]

            resultado =  np.select(condlist=NUMPY_CONDITIONS, choicelist=NUMPY_CHOICES, default=area_rotor)
            return resultado


        ashad = np.array(list(map(lambda x, y, z, w: _koch(x, y, z, w), radio_turbina.flatten(), area_rotor.flatten(), radio_estela.flatten(), d.flatten()))).reshape(n_turbinas, n_turbinas)
        ashad[np.isnan(ashad)] = 0
 
        beta = ashad / area_rotor

        difference = estela_ji - temp_vel_ti
        squared_difference = difference ** 2

        suma = np.sum(beta * squared_difference * rectificador, axis=1)       

        
        # Velocidad perturbada por efecto estela
        vel_perturbada = temp_vel_ti - np.sqrt(suma)
        vel_perturbada = np.where(np.isnan(vel_perturbada) == True, temp_vel_ti, vel_perturbada)

        # Filtro por velocidad negativa
        vel_perturbada = np.where(vel_perturbada < 0, 0, vel_perturbada)

        return pd.Series(vel_perturbada, index=n_estampa_df[1]['id_turbina']).sort_index().values
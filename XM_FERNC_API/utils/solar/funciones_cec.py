import xm_solarlib


def transformar_tec(t: str):
    """
    Transforma la tecnología de un módulo fotovoltaico a un formato estándar.

    Parámetros:
    - t (str): Cadena que representa la tecnología del módulo fotovoltaico.

    Retorno:
    - str: Tecnología del módulo fotovoltaico en un formato estándar.
    """
    technology_mapping = {
        "Mono-c-Si": "monoSi",
        "monoSi": "monoSi",
        "monosi": "monoSi",
        "c-Si": "monoSi",
        "xsi": "monoSi",
        "mtSiMono": "monoSi",
        "Multi-c-Si": "multiSi",
        "multiSi": "multiSi",
        "multisi": "multiSi",
        "mc-Si": "multiSi",
        "EFG mc-Si": "multiSi",
        "polySi": "poliSi",
        "polysi": "poliSi",
        "mtSiPoly": "poliSi",
        "CIS": "cis",
        "cis": "cis",
        "CIGS": "cigs",
        "cigs": "cigs",
        "CdTe": "cdte",
        "cdte": "cdte",
        "Thin Film": "cdte",
        "GaAs": "cdte",
        "amorphous": "amorphous",
        "asi": "amorphous",
        "a-Si / mono-Si": "amorphous",
        "2-a-Si": "amorphous",
        "3-a-Si": "amorphous",
        "Si-Film": "amorphous",
        "HIT-Si": "amorphous",
    }

    module_tec = technology_mapping.get(t)
    return module_tec


def obtener_parametros_fit_cec_sam(params_modulo):
    """
    Obtiene los parámetros de ajuste CEC-SAM para un módulo fotovoltaico.

    Parámetros:
    - params_modulo: Parámetros del módulo fotovoltaico.

    Retorno:
    - pd.DataFrame: DataFrame que contiene los parámetros de ajuste CEC-SAM.
    """
    m_tec = transformar_tec(params_modulo.Tecnologia.Value)
    result = xm_solarlib.ivtools.sdm.fit_cec_sam(
        celltype=m_tec,
        v_mp=params_modulo.Vmpstc,
        i_mp=params_modulo.Impstc,
        v_oc=params_modulo.Vocstc,
        i_sc=params_modulo.Iscstc,
        alpha_sc=(params_modulo.AlphaSc / 100) * params_modulo.Iscstc,
        beta_voc=(params_modulo.BetaOc / 100) * params_modulo.Vocstc,
        gamma_pmp=params_modulo.GammaPmp,
        cells_in_series=params_modulo.Ns,
        temp_ref=25,
    )
    return result


def obtener_parametros_circuito_eq(df_array, params_modulo, params_fit_cec_sam):
    """
    Calcula los parámetros del modelo de circuito equivalente para un módulo fotovoltaico.

    Parámetros:
    - df_array: DataFrame que contiene la irradiancia efectiva y la temperatura del panel solar.
    - params_modulo: Parámetros del módulo fotovoltaico.
    - params_fit_cec_sam: Parámetros de ajuste CEC-SAM.

    Retorno:
    - pd.DataFrame: DataFrame que contiene los parámetros del modelo de circuito equivalente.
    """
    result = xm_solarlib.pvsystem.calcparams_cec(
        effective_irradiance=df_array.poa,
        temp_cell=df_array.temp_panel,
        alpha_sc=params_modulo.AlphaSc,
        i_l_ref=params_fit_cec_sam[0],
        i_o_ref=params_fit_cec_sam[1],
        r_s=params_fit_cec_sam[2],
        r_sh_ref=params_fit_cec_sam[3],
        a_ref=params_fit_cec_sam[4],
        adjust=params_fit_cec_sam[5],
        egref=1.121,
        degdt=0.0002677,
    )
    return result

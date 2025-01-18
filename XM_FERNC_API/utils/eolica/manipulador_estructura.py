import copy
from typing import Dict, Tuple

from XM_FERNC_API.infraestructura.models.eolica.parametros import JsonModelEolica
from XM_FERNC_API.utils.manipulador_dataframe import ManipuladorDataframe
from XM_FERNC_API.utils.eolica.dataclasses_eolica import Aerogenerador, Modelo, Pcc


class ManipuladorEstructura:
    def __init__(self) -> None:
        self.manipulador_df = ManipuladorDataframe()

    def crear_dict_modelos_aerogeneradores(self, params: JsonModelEolica)-> Tuple[Dict, Dict]:
        """
        Crea diccionarios de modelos y aerogeneradores a partir de los parámetros de configuración proporcionados.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - params: Un objeto JsonModelEolica que contiene parámetros de configuración para la modelización eólica.

        Retorno:
        - Tuple: Una tupla que contiene un diccionario de modelos de aerogeneradores y un diccionario de objetos de aerogeneradores.
        """
        modelos_dict = {}
        aero_dict = {}

        for modelo in params.ParametrosConfiguracion.Aerogeneradores:
            modelo_specs = Modelo(
                modelo.ModeloAerogenerador,
                modelo.AlturaBuje,
                modelo.DiametroRotor,
                modelo.PotenciaNominal,
                modelo.VelocidadNominal,
                modelo.DensidadNominal,
                modelo.VelocidadCorteInferior,
                modelo.VelocidadCorteSuperior,
                modelo.TemperaturaAmbienteMinima,
                modelo.TemperaturaAmbienteMaxima,
                modelo.CurvasDelFabricante,
            )

            modelos_dict[modelo.ModeloAerogenerador] = modelo_specs

            for aero in modelo.EspecificacionesEspacialesAerogeneradores:
                aerogenerador = Aerogenerador(
                    aero.Aerogenerador,
                    aero.MedicionAsociada.Value,
                    aero.Latitud,
                    aero.Longitud,
                    aero.Elevacion,
                    modelo.ModeloAerogenerador,
                )

                aero_dict[aerogenerador.id_aero] = aerogenerador

        for aero in aero_dict.values():
            aero.curvas_fabricante = copy.deepcopy(
                modelos_dict[aero.modelo].curvas_fabricante
            )

        return modelos_dict, aero_dict
    
    def agregar_pcc(
        self, params: JsonModelEolica, aerogeneradores: Dict
    ) -> Dict:
        """
        Agrega un objeto PCC al diccionario aerogeneradores.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - params: Un objeto JsonModelEolica que contiene parámetros de configuración para la modelización eólica.
        - aerogeneradores: Un diccionario que contiene objetos Aerogenerador.

        Retorno:
        - aerogeneradores (Dict): El diccionario aerogeneradores con el objeto PCC como ultimo punto de conexion.
        """
        params_trans = params.ParametrosTransversales

        aerogeneradores["pcc"] = Pcc(
            params_trans.Latitud,
            params_trans.Longitud,
            params_trans.Elevacion,
            params_trans.Voltaje,
        )

        return aerogeneradores

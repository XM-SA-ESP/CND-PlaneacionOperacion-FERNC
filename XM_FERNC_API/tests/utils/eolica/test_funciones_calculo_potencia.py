import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo, CurvasDelFabricante
from infraestructura.models.eolica.parametros import JsonModelEolica, ParametrosTransversales, ParametrosConfiguracion, ArchivoSeries
from utils.eolica.funciones_calculo_potencia import CalculoPotencia

class TestCalculoPotencia(unittest.TestCase):
    def setUp(self):
        self.calculo_potencia = CalculoPotencia()

    def test_potencia_planta_eolica(self):
        # Mock de datos para el test
        aerogeneradores = {
            "aero1": Aerogenerador(id_torre="Torre1", latitud=40.0, modelo="modelo1", longitud=-3.0, 
                                   elevacion=100.0, id_aero=1, df=pd.DataFrame({"PotenciaAjustada": [100, 150, 200]})),
            "aero2": Aerogenerador(id_torre="Torre2", latitud=40.0, modelo="modelo2", longitud=-3.0,
                                    elevacion=100.0, id_aero=2, df=pd.DataFrame({"PotenciaAjustada": [120, 130, 180]})),
        }

        params_config = ParametrosConfiguracion(
            SistemasDeMedicion=None,
            Aerogeneradores=[],
            ParametroConexion=[],
        )

        params_series = ArchivoSeries(Nombre="SeriesTest")

        params_trans = ParametrosTransversales(
            Offshore=False,
            Elevacion=100.0,
            Voltaje=1.0,
            NombrePlanta="Planta1",
            Cen=10.0,
            Ihf=10.0,
            Ppi=500.0,
            Kpc=10.0,
            Kt=5.0,
            Kin=2.0,
            Latitud=40.0,
            Longitud=-3.0,
            InformacionMedida=True,
        )
       
        params = JsonModelEolica(ParametrosTransversales=params_trans, ParametrosConfiguracion=params_config, ArchivoSeries=params_series)
        params.ParametrosTransversales = params_trans

        # Llamada al método
        result = self.calculo_potencia.potencia_planta_eolica(aerogeneradores, params)

        # Verificación del resultado
        self.assertEqual(result.tolist(), [198.0, 252.0, 342.0])

    def test_interpolar_potencia(self):
        # Mock de datos para el test
        curva_vel = np.array([5, 10, 15])
        curva_potencia = np.array([100, 200, 300])

        # Llamada al método
        result = self.calculo_potencia.interpolar_potencia(12, curva_vel, curva_potencia)

        # Verificación del resultado
        self.assertEqual(result, 240)

    """
    def test_calcular_potencia_aerogeneradores(self):
            
        aerogeneradores = {
            1: Aerogenerador(
                id_torre="Torre1",
                id_aero=1,
                latitud=40.0,
                modelo="modelo1",
                longitud=-3.0,
                elevacion=100.0,
                df=pd.DataFrame({"VelocidadEstela": [5, 10, 15], "Ta": [20, 25, 30]}),
            ),
            2: Aerogenerador(
                id_torre="Torre2",
                id_aero=2,
                latitud=40.0,
                modelo="modelo2",
                longitud=-3.0,
                elevacion=100.0,
                df=pd.DataFrame({"VelocidadEstela": [12, 18, 22], "Ta": [22, 26, 28]}),
            ),
        }

        cf = CurvasDelFabricante(
                    SerieVelocidad=1.0,
                    SeriePotencia=2.0,
                    SerieCoeficiente=0.5,
                    SerieVcthCorregida=0.0,
                )

        modelos = {
            "modelo1": Modelo(
                nombre="Modelo1",
                altura_buje=80.0,
                diametro_rotor=120.0,
                p_nominal=2000.0,
                v_nominal=15.0,
                den_nominal=1.225,
                v_min=3.0,
                v_max=25.0,
                t_min=-10.0,
                t_max=40.0,
                curvas_fabricante=cf,
            ),
            "modelo2": Modelo(
                nombre="Modelo2",
                altura_buje=80.0,
                diametro_rotor=120.0,
                p_nominal=2000.0,
                v_nominal=15.0,
                den_nominal=1.225,
                v_min=3.0,
                v_max=25.0,
                t_min=-10.0,
                t_max=40.0,
                curvas_fabricante=cf,
            ),
        }
        

        # Llamada al método
        result = self.calculo_potencia.calcular_potencia_aerogeneradores(aerogeneradores, modelos)

        # Verificación del resultado
        self.assertEqual(result[1].df["Potencia"].tolist(), [200, 300, 0])
        self.assertEqual(result[2].df["Potencia"].tolist(), [0, 0, 0])
    """

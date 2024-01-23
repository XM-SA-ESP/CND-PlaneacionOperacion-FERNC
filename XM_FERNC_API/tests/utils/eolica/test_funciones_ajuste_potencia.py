import unittest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from infraestructura.models.eolica.parametros import ParametrosTransversales, CurvasDelFabricante
from utils.eolica.funciones_ajuste_potencia import AjustePotencia
from utils.eolica.dataclasses_eolica import Modelo, Aerogenerador

class TestAjustePotencia(unittest.TestCase):
    def setUp(self):
        self.ajuste_potencia = AjustePotencia()

    def test_obtener_pi_pc1(self):
        result = self.ajuste_potencia._AjustePotencia__obtener_pi_pc1(100, 1.225, 1.0)
        self.assertAlmostEqual(result, 122.50000000000001, places=10)

    def test_obtener_pi_pc2(self):
        result = self.ajuste_potencia._AjustePotencia__obtener_pi_pc2(100, 0.02, 1.0, 5.0)
        self.assertAlmostEqual(result, 99.0, places=10)

    def test_obtener_pi_pc3(self):
        result = self.ajuste_potencia._AjustePotencia__obtener_pi_pc3(98.0, 10, 5, 2)
        self.assertAlmostEqual(result, 82.1142, places=3)

    def test_ajuste_potencia_aerogeneradores(self):
       
        params_trans = ParametrosTransversales(
            Offshore=False,
            Elevacion=100.0,
            Voltaje=1.0,
            NombrePlanta="Planta1",
            Cen=10.0,
            Ihf=20.0,
            Ppi=30.0,
            Kpc=10.0,
            Kt=5.0,
            Kin=2.0,
            Latitud=40.0,
            Longitud=-3.0,
            InformacionMedida=True,
        )

        curvas_fabricante = CurvasDelFabricante(
            SerieVelocidad=1.0,
            SeriePotencia=2.0,
            SerieCoeficiente=0.5,
            SerieVcthCorregida=0.0,
        )

        modelo_aerogenerador = Modelo(
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
            curvas_fabricante=curvas_fabricante,
        )

        df_aerogenerador = pd.DataFrame({
            "DenBuje": [1.0, 1.2, 1.5],
            "Potencia": [1000.0, 1500.0, 2000.0],
        })

        aerogenerador = Aerogenerador(
            id_aero=1,
            id_torre="Torre1",
            latitud=40.0,
            longitud=-3.0,
            elevacion=100.0,
            modelo="Modelo1",
            dist_pcc=1.0,
            df=df_aerogenerador,
        )

        ajuste_potencia = AjustePotencia()
        result = ajuste_potencia.ajuste_potencia_aerogeneradores(
            params_trans, {1: aerogenerador}, {"Modelo1": modelo_aerogenerador}, -123
        )
        
        # Verifica que el DataFrame de cada aerogenerador tenga la columna "PotenciaAjustada"
        print(result)
        for aero in result.values():
            self.assertIn("PotenciaAjustada", aero.df.columns)

        # Verifica que la función de ajuste ha sido aplicada correctamente
        self.assertAlmostEqual(result[1].df["PotenciaAjustada"].iloc[0], 2000.0, places=3)
        self.assertAlmostEqual(result[1].df["PotenciaAjustada"].iloc[1], 2000.0, places=3)
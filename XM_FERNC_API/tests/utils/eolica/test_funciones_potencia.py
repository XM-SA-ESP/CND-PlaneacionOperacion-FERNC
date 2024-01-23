import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from utils.eolica.funciones_calculo_potencia import CalculoPotencia
from utils.eolica.dataclasses_eolica import Aerogenerador, Pcc, CurvasDelFabricante


class TestCalculoPotencia(unittest.TestCase):
    def setUp(self):
        self.calculo_potencia = CalculoPotencia()

    def test_potencia_planta_eolica(self):
        mock_aerogeneradores = {
            "aero1": MagicMock(df=pd.DataFrame({"PotenciaAjustada": [200, 300]})),
            "aero2": MagicMock(df=pd.DataFrame({"PotenciaAjustada": [150, 250]})),
        }
        mock_params = MagicMock()
        mock_params.ParametrosTransversales.Ihf = 10
        mock_params.ParametrosTransversales.Ppi = 1000

        result = self.calculo_potencia.potencia_planta_eolica(
            mock_aerogeneradores, mock_params
        )

        # result es una pd.Series
        self.assertIsInstance(result, pd.Series)
        self.assertTrue((result <= 1000).all())

    def test_interpolar_potencia(self):
        viento = 8
        curva_vel = np.array([4, 8, 12])
        curva_potencia = np.array([100, 200, 300])

        result = self.calculo_potencia.interpolar_potencia(
            viento, curva_vel, curva_potencia
        )

        self.assertIsInstance(result, float)
        self.assertEqual(result, 200)

    def test_calcular_potencia_aerogeneradores(self):
        mock_aerogeneradores = {
            "aero1": MagicMock(
                modelo="modelo1",
                df=pd.DataFrame({"VelocidadEstela": [4, 12], "Ta": [25, 15]}),
            ),
            "aero2": MagicMock(
                modelo="modelo2",
                df=pd.DataFrame({"VelocidadEstela": [5, 10], "Ta": [20, 10]}),
            ),
        }
        mock_modelos = {
            "modelo1": MagicMock(
                v_min=3,
                v_max=15,
                t_min=0,
                t_max=50,
                curva_vel=np.array([4, 8, 12]),
                curva_potencia=np.array([100, 200, 300]),
            ),
            "modelo2": MagicMock(
                v_min=3,
                v_max=15,
                t_min=0,
                t_max=50,
                curva_vel=np.array([4, 8, 12]),
                curva_potencia=np.array([50, 150, 250]),
            ),
        }

        with patch(
            "utils.eolica.funciones_calculo_potencia.CorreccionVelocidadParque"
        ) as mock_correccion:
            mock_correccion.obtener_curvas_potencia_velocidad.side_effect = [
                (
                    mock_modelos["modelo1"].curva_vel,
                    mock_modelos["modelo1"].curva_potencia,
                ),
                (
                    mock_modelos["modelo2"].curva_vel,
                    mock_modelos["modelo2"].curva_potencia,
                ),
            ]

            result = self.calculo_potencia.calcular_potencia_aerogeneradores(
                mock_aerogeneradores, mock_modelos
            )

            self.assertIsInstance(result, dict)
            for aero in result.values():
                self.assertIn("Potencia", aero.df.columns)

    def test_interpolar_potencia_longitud_diferente(self):
        curva_vel = np.array([4, 8, 12])
        curva_potencia = np.array([100, 200])  # Longitud intencionadamente incorrecta

        with self.assertRaises(ValueError):
            self.calculo_potencia.interpolar_potencia(10, curva_vel, curva_potencia)

    @patch("utils.eolica.funciones_calculo_potencia.CorreccionVelocidadParque")
    def test_calcular_potencia_aerogeneradores(self, mock_correccion):
        # Crear mocks para los objetos Aerogenerador y sus DataFrames
        aero1 = Aerogenerador(
            id_aero="id1",
            id_torre="torre1",
            latitud=40.0,
            longitud=-3.0,
            elevacion=10.0,
            modelo="modelo1",
        )
        aero1.df = pd.DataFrame({"VelocidadEstela": [5, 12], "Ta": [15, 20]})
        aero2 = Aerogenerador(
            id_aero="id2",
            id_torre="torre2",
            latitud=41.0,
            longitud=-4.0,
            elevacion=20.0,
            modelo="modelo2",
        )
        aero2.df = pd.DataFrame({"VelocidadEstela": [6, 13], "Ta": [10, 25]})

        # Crear un diccionario de aerogeneradores
        aerogeneradores = {"aero1": aero1, "aero2": aero2}

        # Crear un diccionario de modelos con curvas de potencia y velocidad
        modelos = {
            "modelo1": MagicMock(v_min=4, v_max=14, t_min=5, t_max=25),
            "modelo2": MagicMock(v_min=3, v_max=15, t_min=0, t_max=30),
        }

        # Configurar el mock de obtener_curvas_potencia_velocidad
        mock_correccion.obtener_curvas_potencia_velocidad.side_effect = [
            (np.array([4, 8, 12]), np.array([100, 200, 300])),
            (np.array([3, 7, 11]), np.array([50, 150, 250])),
        ]

        # Llamar a la función que se está probando
        result = self.calculo_potencia.calcular_potencia_aerogeneradores(
            aerogeneradores, modelos
        )

        # Asegurarse de que cada aerogenerador tiene una columna 'Potencia' en su DataFrame
        for aero in result.values():
            self.assertIn("Potencia", aero.df.columns)

        # Asegurarse de que los valores de potencia están dentro de los límites esperados
        for aero in result.values():
            for potencia in aero.df["Potencia"]:
                self.assertTrue((potencia >= 0) and (potencia <= 300))

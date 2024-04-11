import json
import unittest

import numpy as np
import pandas as pd

from unittest.mock import MagicMock

from infraestructura.models.eolica.parametros import CurvasDelFabricante
from utils.eolica.dataclasses_eolica import Modelo, Aerogenerador
from utils.eolica.funciones_correccion_velocidad_parque_eolico import CorreccionVelocidadParque
from utils.eolica.caracterizacion_estela import Estela


class TestCorreccionVelocidadParque(unittest.TestCase):
    def setUp(self):
        self.correccion_velocidad = CorreccionVelocidadParque()
        with open("./tests/data/test_json_data_eolica.json", "r") as file:
            test_json = json.load(file)

        self.params = test_json

    def test_velocidad_corregida_sin_recuperacion(self):
        result = self.correccion_velocidad._CorreccionVelocidadParque__velocidad_corregida_sin_recuperacion(
            h_prima=80.0,
            z_prima=0.1,
            vel_viento=10.0,
            z_o1=0.01,
            z_o2=0.02
        )
        self.assertAlmostEqual(result, 7.57384, places=3)

    def test_velocidad_corregida_con_recuperacion(self):
        result = self.correccion_velocidad._CorreccionVelocidadParque__velocidad_corregida_con_recuperacion(
            vel_viento=10.0,
            vel_corregida=9.0,
            x_dist=600.0,
            x_inicio=2400.0,
            x_50=4000.0
        )
        self.assertAlmostEqual(result, 8.633, places=1)

    def test_z_prima_mayor(self):
        result = self.correccion_velocidad._CorreccionVelocidadParque__z_prima_mayor(
            vel_viento=10.0,
            z_prima=80.0,
            h_prima=100.0,
            z_o1=0.01,
            z_o2=0.02
        )
        self.assertAlmostEqual(result, 10.17763, places=3)

    def test_z_prima_menor(self):
        result = self.correccion_velocidad._CorreccionVelocidadParque__z_prima_menor(
            vel_viento=10.0,
            z_prima=0.1,
            h_prima=100.0,
            z_o1=0.01,
            z_o2=0.02
        )
        self.assertAlmostEqual(result, 7.5585, places=3)

    def test_altura_capa_limite_interna(self):
        result = self.correccion_velocidad._CorreccionVelocidadParque__altura_capa_limite_interna(
            h=100.0,
            x=600.0,
            z_02=0.02
        )
        self.assertAlmostEqual(result, 211.71931, places=3)

    def test_calculo_h_z_prima(self):
        diametro = 80.0
        x_dist = 600.0
        h_buje = 100.0
        h_buje_promedio = 90.0
        z_o2 = 0.02
        h_prima, z_prima = self.correccion_velocidad._CorreccionVelocidadParque__calculo_h_z_prima(
            diametro, x_dist, h_buje, h_buje_promedio, z_o2
        )
        self.assertAlmostEqual(h_prima, 134.73099, places=3)
        self.assertAlmostEqual(z_prima, h_buje - (diametro/2), places=2)

    def test_velocidad_corregida_sin_recuperacion(self):
        h_prima = 600.0
        z_prima = 100.0
        vel_viento = 90.0
        z_o1 = 0.01
        z_o2 = 0.02
        resultado = self.correccion_velocidad._CorreccionVelocidadParque__velocidad_corregida_sin_recuperacion(
            h_prima, z_prima, vel_viento, z_o1, z_o2
        )
        self.assertAlmostEqual(resultado, 89.2276, places=3)
    

    def test_calcular_h_buje_promedio(self):
        aero_1 = MagicMock(spec=Aerogenerador, modelo="modelo_1")
        aero_2 = MagicMock(spec=Aerogenerador, modelo="modelo_2")

        modelo_1 = MagicMock(spec=Modelo, nombre = "modelo_1", altura_buje = 50.0)
        modelo_2 = MagicMock(spec=Modelo, nombre = "modelo_2", altura_buje = 70.0)


        aero_dict = {"a": aero_1, "b": aero_2}
        modelo_dict = {"modelo_1": modelo_1, "modelo_2":modelo_2}

        resultado = self.correccion_velocidad.calcular_h_buje_promedio(modelo_dict, aero_dict)
        self.assertAlmostEqual(resultado, 60.0)

    
    def test_obtener_curvas_potencia_velocidad(self):
        curvas_fabricante = [
            CurvasDelFabricante(
                SerieVelocidad=1.0,
                SeriePotencia=0.0,
                SerieCoeficiente=0.0,
                SerieVcthCorregida=0,
            ),
            CurvasDelFabricante(
                SerieVelocidad=2.0,
                SeriePotencia=3.6,
                SerieCoeficiente=1.0,
                SerieVcthCorregida=0,
            ),
        ]
        modelo_test = MagicMock(spec=Modelo, curvas_fabricante=curvas_fabricante)
        curva_vel, curva_potencia = self.correccion_velocidad.obtener_curvas_potencia_velocidad(modelo_test)
        self.assertTrue(isinstance(curva_vel, np.ndarray))
        self.assertTrue(isinstance(curva_potencia, np.ndarray))


    def test_correccion_velocidad_parque_eolico(self):
        aero1 = Aerogenerador(
            id_torre="Torre1",
            latitud=12.292,
            modelo="modelo_test",
            longitud=-71.22,
            elevacion=1,
            id_aero=1,
            df=pd.DataFrame(
                {"VelocidadViento": [8.12, 8.26, 8.34], "DireccionViento": [71.36, 73.22, 75.28], "DenBuje": [1.32, 1.34, 1.33]},
                index=["2012-01-01", "2012-01-03", "2012-01-03"],
            ),
        )
        aero2 = Aerogenerador(
            id_torre="Torre2",
            latitud=12.287,
            modelo="modelo_test",
            longitud=-71.22,
            elevacion=2.0,
            id_aero=2,
            df=pd.DataFrame(
                {"VelocidadViento": [8.12, 8.26, 8.34], "DireccionViento": [71.36, 73.22, 75.28], "DenBuje": [1.32, 1.34, 1.33]},
                index=["2012-01-01", "2012-01-02", "2012-01-03"],
            ),
        )

        cf = [
            CurvasDelFabricante(SerieVelocidad=1.0, SeriePotencia=3.0, SerieCoeficiente=2.0, SerieVcthCorregida=3),
            CurvasDelFabricante(SerieVelocidad=2.0, SeriePotencia=3.6, SerieCoeficiente=1.0, SerieVcthCorregida=3)
        ]

        modelo_test = Modelo(
            nombre="modelo_test",
            altura_buje=98.0,
            diametro_rotor=92.0,
            p_nominal=2350.0,
            v_nominal=14.0,
            den_nominal=1.23,
            v_min=2.0,
            v_max=25.0,
            t_min=-10.0,
            t_max=40.0,
            curvas_fabricante=cf,
        )
        result_list = []
        for v, aero_id in self.correccion_velocidad.correccion_velocidad_parque_eolico(
            fecha = '2012-01-01',
            ordenamiento = [1, 2],
            aerogeneradores = {1: aero1, 2: aero2},
            modelos = {"modelo_test": modelo_test},
            h_buje_promedio = 980.0,
            offshore = True,
            z_o1 = 0.03,
            z_o2 = 0.002,
        ):
            result_list.append((aero_id, v))

        self.assertEqual(result_list, [(2, 8.713193673143397)])

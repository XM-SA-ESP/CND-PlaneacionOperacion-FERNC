import unittest
import datetime
import numpy as np
import pandas as pd
from unittest.mock import MagicMock
from utils.eolica.caracterizacion_estela import Estela
from infraestructura.models.eolica.parametros import JsonModelEolica
from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo, CurvasDelFabricante


class TestEstela(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_caracterizacion_estela(self):
        fecha = '2012-01-01'
        aero1 = Aerogenerador(id_torre="Torre1", latitud=40.0, modelo="modelo1", longitud=-3.0,
                              elevacion=100.0, id_aero=1, df=pd.DataFrame({"VelocidadViento": [100, 200, 300]}, index=['2012-01-01', '2014-04-01', '2013-07-01']))
        aero2 = Aerogenerador(id_torre="Torre2", latitud=40.0, modelo="modelo2", longitud=-3.0,
                              elevacion=100.0, id_aero=2, df=pd.DataFrame({"DenBuje": [100, 200, 300]}, index=['2012-01-01', '2014-04-01', '2013-07-01']))

        cf = MagicMock()

        modelo_j = Modelo(
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
        )
        cre = 0.5
        x_dist = 250.0
        vel_viento_j = 15.0
        curva_coef = np.array([0.1, 0.2, 0.3])
        curva_vcth = np.array([10.0, 15.0, 20.0])
        theta_j = 45.0
        x_lon_i_j = 10.0
        x_lat_i_j = 20.0
        elevacion_j = 50.0
        h_buje_j = 80.0
        influencia_acumulada = 0.0

        estela_calculadora = Estela()

        result = estela_calculadora.caracterizacion_estela(
            fecha, aero1, aero2, modelo_j, cre, x_dist,
            vel_viento_j, curva_coef, curva_vcth, theta_j,
            x_lon_i_j, x_lat_i_j, elevacion_j, h_buje_j, influencia_acumulada
        )
        vel_j_estela, vel_influencia_estela = result
        self.assertAlmostEqual(vel_j_estela, 100.0, places=2) 
        self.assertAlmostEqual(vel_influencia_estela, 0.0)

        #test cuando x_dist < 0
        x_dist = -90.0
        result = estela_calculadora.caracterizacion_estela(
            fecha, aero1, aero2, modelo_j, cre, x_dist,
            vel_viento_j, curva_coef, curva_vcth, theta_j,
            x_lon_i_j, x_lat_i_j, elevacion_j, h_buje_j, influencia_acumulada
        )
        vel_j_estela, vel_influencia_estela = result
        self.assertAlmostEqual(vel_j_estela, 100.0, places=2) 
        self.assertAlmostEqual(vel_influencia_estela, 0.0)

    def test_calculo_r_estela(self):
        estela = Estela()
        resultado = estela._Estela__calculo_r_estela(10, 0.5, 20)
        self.assertAlmostEqual(resultado, 15.0, places=2)  

    def test_calculo_coef_empuje(self):
        estela = Estela()
        resultado = estela._Estela__calculo_coef_empuje(0.5, 1.225, 1.0)  
        self.assertAlmostEqual(resultado, 0.6125, places=2) 

    def test_obtener_c_fabricante(self):
        estela = Estela()
        vel_viento = 10  
        cur_vcth = np.array([5, 10, 15])  
        cur_coef_empuje = np.array([0.2, 0.3, 0.4])  
        resultado = estela._Estela__obtener_c_fabricante(vel_viento, cur_vcth, cur_coef_empuje)
        self.assertAlmostEqual(resultado, 0.3, places=2)

    def test_obtener_velocidad_estela(self):
        estela = Estela()
        resultado = estela._Estela__obtener_velocidad_estela(10, 10, 10, 0.5)
        self.assertAlmostEqual(resultado, 9.268, places=3)

    def test_obtener_r_x_dist(self):
        estela = Estela()
        resultado = estela._Estela__obtener_r_x_dist(0.5)
        self.assertEqual(resultado, 1)

    def test_obtener_centro_estela(self):
        estela = Estela()
        resultado = estela._Estela__obtener_centro_estela(10, 10, 10, 0.5, 5, 50, 1)
        self.assertAlmostEqual(resultado[0], 1.224, places=2)

    def test_obtener_distancia_estela_aero(self):
        estela = Estela()
        resultado = estela._Estela__obtener_distancia_estela_aero(10, 10, np.array([1.224, 10.5, 55.5]), 5, 50, 1)
        self.assertAlmostEqual(resultado, 8.80444069773884, places=3)

    def test_obtener_area_rotor(self):
        estela = Estela()
        resultado = estela._Estela__obtener_area_rotor(10)
        self.assertAlmostEqual(resultado, 314.15926, places=2)

    def test_obtener_area_efecto_estela(self):
        
        estela = Estela()
        resultado = estela._Estela__obtener_area_efecto_estela(15.0, 10.0, 5.0, 5.0, 78.54)
        self.assertAlmostEqual(resultado, 0.0, places=2)

    def test_obtener_bj(self):
        estela = Estela()
        resultado = estela._Estela__obtener_bj(54.86, 78.54)
        self.assertAlmostEqual(resultado, 0.698, places=3)

    def test_obtener_vel_influencia_estela(self):
        estela = Estela()
        resultado = estela._Estela__obtener_vel_influencia_estela(0.698, 0.866, 10, 1)
        self.assertAlmostEqual(resultado, 58.234, places=3)

    def test_obtener_vel_j_estela(self):
        estela = Estela()
        resultado = estela._Estela__obtener_vel_j_estela(10, 0.072)
        self.assertAlmostEqual(resultado, 9.732, places=3)

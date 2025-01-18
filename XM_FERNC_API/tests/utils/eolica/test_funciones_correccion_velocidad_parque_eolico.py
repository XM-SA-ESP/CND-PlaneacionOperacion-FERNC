import json
import unittest

import numpy as np
import pandas as pd

from unittest.mock import MagicMock, patch

from infraestructura.models.eolica.parametros import CurvasDelFabricante
from utils.eolica.dataclasses_eolica import Modelo, Aerogenerador
from utils.eolica.funciones_correccion_velocidad_parque_eolico import \
    CorreccionVelocidadParque, serialize_curvas_fabricante, serialize_dataframe, serialize_aerogenerador, \
    correccion_velocidad_parque_eolico_solo, calcular_h_buje_promedio, calculo_h_z_prima
from utils.eolica.caracterizacion_estela import Estela
from XM_FERNC_API.utils.manipulador_excepciones import BaseExcepcion


class TestCorreccionVelocidadParque(unittest.TestCase):
    def setUp(self):
        self.correccion_velocidad = CorreccionVelocidadParque()
        self.estela = Estela()

        with open("./tests/data/test_json_data_eolica.json", "r") as file:
            test_json = json.load(file)

        self.params = test_json

        self.aerogeneradores_mock = {
            1: dict(
                id_torre="Torre1",
                latitud=12.292,
                modelo="modelo_test",
                longitud=91.22,
                elevacion=1,
                id_aero=1,
                df=pd.DataFrame(
                    {"VelocidadViento": [8.12, 8.26, 8.34], "DireccionViento": [71.36, 73.22, 75.28], "DenBuje": [1.32, 1.34, 1.33]},
                    index=["2012-01-01", "2012-01-03", "2012-01-03"],
                ),
            ),
            2: dict(
                id_torre="Torre2",
                latitud=15.287,
                modelo="modelo_test",
                longitud=-71.22,
                elevacion=2.0,
                id_aero=2,
                df=pd.DataFrame(
                    {"VelocidadViento": [9.12, 8.26, 8.34], "DireccionViento": [71.36, 73.22, 75.28], "DenBuje": [1.32, 1.34, 1.33]},
                    index=["2012-01-01", "2012-01-02", "2012-01-03"],
                ),
            )
        }

        cf = [
            CurvasDelFabricante(SerieVelocidad=1.0, SeriePotencia=3.0, SerieCoeficiente=2.0, SerieVcthCorregida=3),
            CurvasDelFabricante(SerieVelocidad=2.0, SeriePotencia=3.6, SerieCoeficiente=1.0, SerieVcthCorregida=3)
        ]

        self.modelos_mock = {
                'modelo_test': dict(
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
        }

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


    def test_serialize_curvas_fabricante(self):
        mock_curva1 = MagicMock()
        mock_curva1.SerieVelocidad = 123
        mock_curva1.SeriePotencia = 1345
        mock_curva1.SerieCoeficiente = 2234
        mock_curva1.SerieVcthCorregida = 356
        result = serialize_curvas_fabricante([mock_curva1])
        self.assertEqual(result[0]['SerieVelocidad'], 123)

    def test_serialize_dataframe(self):
        # Crear un DataFrame de prueba
        data = {
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
            'col3': [10.5, 20.5, 30.5]
        }
        df = pd.DataFrame(data)

        # Resultado esperado
        expected_output = {
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
            'col3': [10.5, 20.5, 30.5]
        }

        # Ejecutar la función que queremos probar
        result = serialize_dataframe(df)

        # Aserción para verificar que el resultado es igual al esperado
        self.assertEqual(result, expected_output)
    
    @patch('utils.eolica.funciones_correccion_velocidad_parque_eolico.serialize_curvas_fabricante')  # Mock de serialize_curvas_fabricante
    def test_serialize_aerogenerador(self, mock_serialize_curvas_fabricante):
        # Crear un MagicMock para simular un objeto Aerogenerador
        aerogenerador_mock = MagicMock()
        
        # Definir los atributos que el mock debe tener
        aerogenerador_mock.id_aero = 'aero_1'
        aerogenerador_mock.id_torre = 'torre_1'
        aerogenerador_mock.latitud = 45.67
        aerogenerador_mock.longitud = -75.12
        aerogenerador_mock.elevacion = 300
        aerogenerador_mock.modelo = 'Modelo_X'
        aerogenerador_mock.dist_pcc = 12.5
        aerogenerador_mock.df = 'DataFrame'  # Puede ser cualquier cosa, depende de tu implementación real
        aerogenerador_mock.f_ordenamiento = 'orden_1'
        aerogenerador_mock.curvas_fabricante = 'curvas_mock'

        # Definir lo que debería devolver el mock de serialize_curvas_fabricante
        mock_serialize_curvas_fabricante.return_value = 'curvas_serializadas'

        # Resultado esperado
        expected_output = {
            'id_aero': 'aero_1',
            'id_torre': 'torre_1',
            'latitud': 45.67,
            'longitud': -75.12,
            'elevacion': 300,
            'modelo': 'Modelo_X',
            'dist_pcc': 12.5,
            'df': 'DataFrame',
            'f_ordenamiento': 'orden_1',
            'curvas_fabricante': 'curvas_serializadas'
        }

        # Llamar a la función que queremos probar
        result = serialize_aerogenerador(aerogenerador_mock)

        # Verificar que serialize_curvas_fabricante fue llamado con el atributo curvas_fabricante
        mock_serialize_curvas_fabricante.assert_called_once_with('curvas_mock')

        # Verificar que el resultado es el esperado
        self.assertEqual(result, expected_output)
    
    @patch('utils.eolica.funciones_correccion_velocidad_parque_eolico.velocidad_corregida_con_recuperacion')
    @patch('utils.eolica.funciones_correccion_velocidad_parque_eolico.calculo_h_z_prima')
    def test_correccion_velocidad_parque_eolico_solo(self, mock_calculo_h_z_prima, mock_velocidad_corregida_con_recuperacion):
        
        mock_calculo_h_z_prima.return_value = 123, 456
        mock_velocidad_corregida_con_recuperacion.return_value = 8.12
        
        # Definir los inputs
        fecha = '2012-01-01'
        ordenamiento = [1, 2]
        h_buje_promedio = 980.0,
        offshore = True,
        z_o1 = 0.03,
        z_o2 = 2,

        # Ejecutar la función
        result = correccion_velocidad_parque_eolico_solo(
            fecha, 
            ordenamiento, 
            self.aerogeneradores_mock, 
            self.modelos_mock, 
            h_buje_promedio, 
            z_o1, 
            z_o2
        )

        # Verificar los resultados
        self.assertEqual(result[0][0], 8.12)
        self.assertEqual(result[0][1], 2)

    def test_calcular_h_buje_promedio(self):
        # Mock de los modelos con alturas de buje
        modelos = {
            'modelo_1': MagicMock(altura_buje=100),
            'modelo_2': MagicMock(altura_buje=120),
            'modelo_3': MagicMock(altura_buje=110),
        }

        # Mock de los aerogeneradores que referencian los modelos
        aerogeneradores = {
            'aero_1': MagicMock(modelo='modelo_1'),
            'aero_2': MagicMock(modelo='modelo_2'),
            'aero_3': MagicMock(modelo='modelo_3'),
        }

        # Llamar la función a testear
        h_buje_promedio = calcular_h_buje_promedio(modelos, aerogeneradores)

        # Calcular el promedio esperado manualmente
        expected_h_buje_promedio = (100 + 120 + 110) / 3

        # Aserción para verificar si el valor calculado es correcto
        self.assertAlmostEqual(h_buje_promedio, expected_h_buje_promedio, places=2)

    @patch('utils.eolica.funciones_correccion_velocidad_parque_eolico.scipy_optimize.root_scalar')
    def test_calculo_h_z_prima(self, mock_root_scalar):
        # Definir el valor de retorno para root_scalar
        mock_root_scalar.return_value = MagicMock(root=200)

        # Definir los parámetros de entrada
        diametro = 120.0
        x_dist = np.float64(500.0)
        h_buje = 150.0
        h_buje_promedio = np.float64(140.0)
        z_o2 = 0.2

        # Ejecutar la función
        h_prima, z_prima = calculo_h_z_prima(diametro, x_dist, h_buje, h_buje_promedio, z_o2)

        # Verificar los valores de retorno
        expected_h_prima = 200 + (2 / 3) * h_buje_promedio
        expected_z_prima = h_buje - (diametro / 2)

        self.assertAlmostEqual(h_prima, expected_h_prima, places=2)
        self.assertAlmostEqual(z_prima, expected_z_prima, places=2)

    @patch('utils.eolica.funciones_correccion_velocidad_parque_eolico.scipy_optimize.root_scalar')
    def test_calculo_h_z_prima_exception(self, mock_root_scalar):
        # Simular un error en root_scalar
        mock_root_scalar.side_effect = Exception("error en el cálculo")

        # Definir los parámetros de entrada
        diametro = 120.0
        x_dist = np.float64(500.0)
        h_buje = 150.0
        h_buje_promedio = np.float64(140.0)
        z_o2 = 0.2

        # Verificar que se lanza la excepción correcta
        with self.assertRaises(BaseExcepcion) as context:
            calculo_h_z_prima(diametro, x_dist, h_buje, h_buje_promedio, z_o2)

        self.assertEqual(context.exception.mensaje, 'Error en la corrección del viento por efecto de grandes parques. Verifique los parámetros de los aerogeneradores.')
    
    def test_calcular_h_buje_promedio(self):
        # Simular los modelos
        modelo_mock1 = MagicMock()
        modelo_mock1.altura_buje = 80.0

        modelo_mock2 = MagicMock()
        modelo_mock2.altura_buje = 100.0

        modelos_mock = {
            'modelo_1': modelo_mock1,
            'modelo_2': modelo_mock2,
        }

        # Simular los aerogeneradores
        aerogenerador_mock1 = MagicMock()
        aerogenerador_mock1.modelo = 'modelo_1'

        aerogenerador_mock2 = MagicMock()
        aerogenerador_mock2.modelo = 'modelo_2'

        aerogeneradores_mock = {
            'aero_1': aerogenerador_mock1,
            'aero_2': aerogenerador_mock2,
        }

        # Llamar a la función
        h_buje_promedio = self.correccion_velocidad.calcular_h_buje_promedio(modelos_mock, aerogeneradores_mock)

        # Verificar el resultado esperado
        self.assertEqual(h_buje_promedio, 90.0)

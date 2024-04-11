import json
import pandas as pd
import unittest

from infraestructura.models.eolica.parametros import (
    ConfiguracionAnemometro,
    CurvasDelFabricante,
    JsonModelEolica
)
from utils.eolica.dataclasses_eolica import Aerogenerador, Modelo, Torre
from utils.eolica.funciones_corregir_curvas import CorregirCurvas


class TestCorregirCurvas(unittest.TestCase):

    def setUp(self) -> None:
        self.corregir_curva_instancia = CorregirCurvas()

        with open("./tests/data/test_json_data_eolica.json", "r") as file:
            test_json = json.load(file)

        self.params = JsonModelEolica(**test_json)

    def test_corregir_curvas_con_torre(self):
        cf1 = CurvasDelFabricante(SerieVelocidad=1.0, SeriePotencia=0.0, SerieCoeficiente=0.0, SerieVcthCorregida=0)
        cf2 = CurvasDelFabricante(SerieVelocidad=2.0, SeriePotencia=3.6, SerieCoeficiente=1.0, SerieVcthCorregida=0)
        modelos = {
            "Enercon E92/2.3MW": Modelo(
                nombre="Enercon E92/2.3MW0",
                altura_buje=98.0,
                diametro_rotor=92.8,
                p_nominal=2350.0,
                v_nominal=14.0,
                den_nominal=1.23,
                v_min=2.0,
                v_max=25.0,
                t_min=-10.0,
                t_max=45.0,
                curvas_fabricante=[
                    cf1,
                    cf2
                ])
        }

        aerogeneradores = {
            1: Aerogenerador(
                id_aero=1,
                id_torre='torre_1',
                latitud=12.29263,
                longitud=-71.22642,
                elevacion=1.0,
                modelo='Enercon E92/2.3MW',
                dist_pcc=None,
                df=None,
                f_ordenamiento=0,
                curvas_fabricante=[cf1, cf2]
            ),
            2: Aerogenerador(
                id_aero=2,
                id_torre='torre_1',
                latitud=12.29263,
                longitud=-71.22642,
                elevacion=1.0,
                modelo='Enercon E92/2.3MW',
                dist_pcc=None,
                df=None,
                f_ordenamiento=0,
                curvas_fabricante=[cf1, cf2]
            )
        }

        df_torres = pd.DataFrame({
            "DireccionViento": [
                75.25, 78.42, 76.89
            ], "PresionAtmosferica": [
                990.62, 990.62, 990.62
            ], "Ta": [
                28.11, 27.51, 26.88
            ], "VelocidadViento": [
                8.66, 9.73, 9.62
            ], 
            "DenBuje": [20.0, 20.1, 20.5]
        }, index=[
            "2008-01-01 0:00:00+00:00",
            "2008-01-01 02:00:00+00:00",
            "2008-01-01 03:00:00+00:00"
        ])

        df_torres.index = pd.to_datetime(df_torres.index)

        torres = {"torre_1": Torre(
            id="torre_1", latitud=12.23587, longitud=-7123587, elevacion=0.0, radio_r=10.0, conf_anemometro=[ConfiguracionAnemometro(
                Anemometro=1, AlturaAnemometro=20.0),
                ConfiguracionAnemometro(
                Anemometro=2, AlturaAnemometro=40.0),
                ConfiguracionAnemometro(
                Anemometro=3, AlturaAnemometro=60.0)], archivo_series="nombre _archivo", dataframe=df_torres
        )}

        result = self.corregir_curva_instancia.corregir_curvas_con_torre(
            torres, modelos, aerogeneradores
        )

        self.assertIsNone(result)

    def test_corregir_curvas_sin_torres(self):
        df = pd.DataFrame({
            "DireccionViento": [75.25, 78.42, 76.89],
            "PresionAtmosferica": [990.62, 990.62, 990.62],
            "Ta": [28.11, 27.51, 26.88],
            "VelocidadViento": [8.66, 9.73, 9.62],
            "TaBuje": [27.98, 27.38, 26.75],
            "Pbuje": [988.4456646529, 988.4414689457, 988.4370459906],
            "PVapor": [3758.1907090835, 3618.3817199489, 3477.1764141461],
            "PVaporSaturacion": [3757.1799555829, 3627.931883521, 3496.4188680899],
            "DenBuje": [1.1295587332, 1.1324726019, 1.135513778],

        }, index=[
            "2008-01-01 0:00:00+00:00",
            "2008-01-01 02:00:00+00:00",
            "2008-01-01 03:00:00+00:00"
        ])

        result = self.corregir_curva_instancia.corregir_curvas_sin_torres(
            self.params, df)

        self.assertIsNone(result)

    def test_obtener_promedio_densidad_buje(self):
        serie = pd.Series([20, 50, 20, 5, 5])

        result = self.corregir_curva_instancia.obtener_promedio_densidad_buje(
            serie)

        self.assertEqual(result, 20.0)

        True

    def test_obtener_vp_vcth_corregida(self):
        curvas = CurvasDelFabricante(
            SerieVelocidad=1.0, SeriePotencia=0.0, SerieCoeficiente=0.0, SerieVcthCorregida=0)

        result = self.corregir_curva_instancia.obtener_vp_vcth_corregida(
            curvas, 12.0, 10.0, 45.0, 40.0, 12.0
        )

        self.assertEqual(result, None)

    def test_obtener_vp_vcth_corregida_v_diseño_cero(self):
        curvas = CurvasDelFabricante(
            SerieVelocidad=0.0, SeriePotencia=0.0, SerieCoeficiente=0.0, SerieVcthCorregida=0)

        result = self.corregir_curva_instancia.obtener_vp_vcth_corregida(
            curvas, 12.0, 10.0, 45.0, 40.0, 0
        )

        self.assertEqual(result, None)

    def test_obtener_vp_vcth_corregida_v_fabricante_cero(self):
        curvas = CurvasDelFabricante(
            SerieVelocidad=-1.0, SeriePotencia=2.2, SerieCoeficiente=0.0, SerieVcthCorregida=0)

        result = self.corregir_curva_instancia.obtener_vp_vcth_corregida(
            curvas, 12.0, 10.0, 45.0, 40.0, 12.0
        )

        self.assertEqual(result, None)

    def test___obtener_vel_diseno(self):
        modelo = Modelo(
            nombre="Enercon E92/2.3MW0", altura_buje=98.0, diametro_rotor=92.8, p_nominal=2350.0, v_nominal=14.0, den_nominal=1.23, v_min=2.0, v_max=25.0, t_min=-10.0, t_max=45.0, curvas_fabricante=[
                CurvasDelFabricante(
                    SerieVelocidad=1.0, SeriePotencia=0.0, SerieCoeficiente=0.0, SerieVcthCorregida=0),
                CurvasDelFabricante(
                    SerieVelocidad=2.0, SeriePotencia=3.6, SerieCoeficiente=1.0, SerieVcthCorregida=0)
            ])

        result = self.corregir_curva_instancia._CorregirCurvas__obtener_vel_diseno(
            modelo)

        self.assertEqual(result, 2.0)

import unittest
import xm_solarlib.pvsystem
from unittest.mock import MagicMock

from utils.solar.funciones_pvsystem import (
    crear_array,
    crear_montura_con_seguidores,
    crear_montura_no_seguidores,
)


class TestPVSystem(unittest.TestCase):
    def test_crear_montura_con_seguidores(self):
        params_array = MagicMock()

        result = crear_montura_con_seguidores(params_array)

        self.assertIsInstance(result, xm_solarlib.pvsystem.SingleAxisTrackerMount)
        self.assertEqual(result.axis_tilt, params_array.OElevacion)
        self.assertEqual(result.axis_azimuth, params_array.OAzimutal)
        self.assertEqual(result.max_angle, params_array.OMax)
        self.assertTrue(result.backtrack)
        self.assertEqual(result.gcr, 0.2857142857142857)
        self.assertEqual(result.cross_axis_tilt, 0.0)
        self.assertEqual(result.racking_model, params_array.Racking.Value)

    def test_crear_montura_no_seguidores(self):
        params_array = MagicMock()

        result = crear_montura_no_seguidores(params_array)

        self.assertIsInstance(result, xm_solarlib.pvsystem.FixedMount)
        self.assertEqual(result.surface_azimuth, params_array.OAzimutal)
        self.assertEqual(result.surface_tilt, params_array.OElevacion)
        self.assertEqual(result.racking_model, params_array.Racking.Value)

    def test_crear_array(self):
        montura = MagicMock()
        params_trans = MagicMock()
        params_array = MagicMock()
        nombre = "Test Array"

        result = crear_array(montura, params_trans, params_array, nombre)

        self.assertIsInstance(result, xm_solarlib.pvsystem.Array)
        self.assertEqual(result.name, nombre)
        self.assertEqual(result.mount, montura)
        self.assertEqual(result.albedo, params_trans.Albedo)
        self.assertEqual(result.module_type, "glass_glass")
        self.assertEqual(result.modules_per_string, params_array.CantidadSerie)
        self.assertEqual(result.strings, params_array.CantidadParalero)

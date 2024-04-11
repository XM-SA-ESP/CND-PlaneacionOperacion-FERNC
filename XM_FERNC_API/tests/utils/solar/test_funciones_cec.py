import unittest
import pandas as pd
from unittest import mock

from utils.solar.funciones_cec import (
    obtener_parametros_fit_cec_sam,
    obtener_parametros_circuito_eq,
)


class TestFuncionesCec(unittest.TestCase):
    def test_obtener_parametros_circuito_eq(self):
        df_array = pd.DataFrame({"poa": [100, 200, 300], "temp_panel": [25, 30, 35]})
        params_modulo = mock.Mock(AlphaSc=0.05)
        params_fit_cec_sam = [1, 2, 3, 4, 5, 6]

        result = obtener_parametros_circuito_eq(
            df_array, params_modulo, params_fit_cec_sam
        )

        result_list = result[0].values.tolist()

        expected_result = [0.100, 0.247, 0.441]

        self.assertIsInstance(result, tuple)
        self.assertAlmostEqual(result_list, expected_result)

    def test_obtener_parametros_fit_cec_sam(self):
        params_modulo = mock.MagicMock()
        params_modulo.Tecnologia.value = "monoSi"
        params_modulo.Vmpstc.value = 100
        params_modulo.Impstc.value = 5
        params_modulo.Vocstc.value = 120
        params_modulo.Iscstc.value = 6
        params_modulo.AlphaSc.value = 0.05
        params_modulo.BetaOc.value = 0.02
        params_modulo.GammaPmp.value = 0.003
        params_modulo.Ns.value = 60

        with mock.patch("utils.solar.funciones_cec.xm_solarlib") as mock_xm_solarlib:
            obtener_parametros_fit_cec_sam(params_modulo)

            mock_xm_solarlib.ivtools.sdm.fit_cec_sam.assert_called_once()

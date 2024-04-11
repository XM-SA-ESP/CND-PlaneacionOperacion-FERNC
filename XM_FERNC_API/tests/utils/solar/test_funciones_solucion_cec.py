import unittest
import pandas as pd
from unittest import mock

from utils.solar.funciones_solucion_cec import obtener_solucion_circuito_eq


class TestPVSystem(unittest.TestCase):
    @mock.patch("xm_solarlib.pvsystem.singlediode")
    def test_obtener_solucion_circuito_eq(self, mock_singlediode):
        params_cec_df = pd.DataFrame(
            {
                "photocurrent": [1, 2, 3],
                "saturation_current": [1, 2, 3],
                "resistance_series": [1, 2, 3],
                "resistance_shunt": [1, 2, 3],
                "nNsVth": [1, 2, 3],
            }
        )

        obtener_solucion_circuito_eq(params_cec_df)

        mock_singlediode.assert_called_once_with(
            photocurrent=params_cec_df["photocurrent"],
            saturation_current=params_cec_df["saturation_current"],
            resistance_series=params_cec_df["resistance_series"],
            resistance_shunt=params_cec_df["resistance_shunt"],
            nnsvth=params_cec_df["nNsVth"],
            method="lambertw",
        )

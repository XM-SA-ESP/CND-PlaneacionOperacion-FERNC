import unittest

import pandas as pd
import numpy as np

from utils.eolica.dataclasses_eolica import Aerogenerador
from utils.eolica.funciones_ordenamiento import Ordenamiento


class TestFuncionesOrdenamiento(unittest.TestCase):
    def setUp(self) -> None:
        self.df_aero_mock_1 = pd.DataFrame(
            {"DireccionViento": [71.5, 73.0, 75.8, 77.2]},
            index=["2008-01-01", "2008-02-01", "2008-03-01", "2008-04-01"],
        )
        self.n_estampas = 4
        self.instancia_ordenamiento = Ordenamiento()

        self.ordenamiento_instancia = Ordenamiento()
        self.aerogeneradores_con_df = {
            1: Aerogenerador(
                id_aero=1,
                id_torre="torre_1",
                latitud=12.29263,
                longitud=-71.22642,
                elevacion=1.0,
                modelo="Enercon E92/2.3MW",
                dist_pcc=None,
                df=self.df_aero_mock_1,
                f_ordenamiento=0,
            ),
            2: Aerogenerador(
                id_aero=2,
                id_torre="torre_1",
                latitud=12.28768,
                longitud=-71.22642,
                elevacion=2.0,
                modelo="Enercon E92/2.3MW",
                dist_pcc=None,
                df=self.df_aero_mock_1,
                f_ordenamiento=0,
            ),
        }

    def test_ordenamineto_vectorizado(self):
        resultado = self.instancia_ordenamiento.ordenamiento_vectorizado(
            self.aerogeneradores_con_df, self.n_estampas
        )

        for df in resultado.values():
            assert isinstance(df, pd.DataFrame)

        self.assertAlmostEqual(
            resultado["2008-03-01"]["factor_reordenamiento"][2], -533.597, places=3
        )

    def test_organizacion(self):
        lat1 = -550.41
        lon1 = 0.0
        tj_longitud = np.array([-71.22642, -71.22642])
        tj_latitud = np.array([12.29263, 12.28768])

        resultado_esperado = (
            np.array([-7770414.23629659, -7770414.23629659]),
            np.array([17490669.51853202, 17491219.93341891]),
        )

        resultado = self.instancia_ordenamiento._organizacion(
            lat1, lon1, tj_longitud, tj_latitud
        )

        np.testing.assert_almost_equal(resultado[0], resultado_esperado[0])
        np.testing.assert_almost_equal(resultado[1], resultado_esperado[1])

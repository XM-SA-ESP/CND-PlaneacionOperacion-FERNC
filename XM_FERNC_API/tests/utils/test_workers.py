import unittest
from unittest.mock import MagicMock, patch
from utils.workers import correcciones_worker, wrapper_efecto_estela_vectorizado

from utils.eolica.caracterizacion_estela import Estela

class TestCorreccionesWorker(unittest.TestCase):

    @patch("utils.eolica.funciones_correccion_velocidad_parque_eolico.CorreccionVelocidadParque.correccion_velocidad_parque_eolico")
    def test_correcciones_worker(self, mock_correccion_velocidad_parque):        
        mock_correccion_velocidad_parque.return_value = [(123.456, "aero_id_1")]
        fecha = '2023-11-13'
        ordenamiento = ['ordenamiento']
        aerogeneradores_dict = {"aero_id_1": MagicMock(), "aero_id_2": MagicMock(), "o": MagicMock()}
        modelos_dict = {"modelo_1": MagicMock(), "modelo_2": MagicMock()}
        h_buje_promedio = 80.0
        offshore = True
        z_o1 = 0.02
        z_o2 = 0.03
        cre = 0.04

        args = (
            fecha,
            ordenamiento,
            aerogeneradores_dict,
            modelos_dict,
            h_buje_promedio,
            offshore,
            z_o1,
            z_o2,
        )

        # Asignar el método de prueba como efecto secundario del objeto mock
        result = correcciones_worker(args)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], fecha)
        self.assertIsInstance(result[1], list)
        self.assertEqual(len(result[1]), 1)  
        self.assertEqual(result[1], [("aero_id_1", 123.456)])

    @patch.object(Estela, "efecto_estela_vectorizado")
    @patch.object(Estela, "_vecdir_tj")
    def test_wrapper_efecto_estela_vectorizado(self, mock_estela_vectorizado, mock_vecdir_tj):
        offshore = True
        cre = 0.02
        caracteristicas_tij = MagicMock()
        densidad = MagicMock()
        dataset = MagicMock()
        n_turbinas = MagicMock()
        curvas_xarray = MagicMock()
        n_estampa_df = MagicMock()

        resultado = wrapper_efecto_estela_vectorizado(
            offshore,
            cre,
            caracteristicas_tij,
            densidad,
            dataset,
            n_turbinas,
            curvas_xarray,
            n_estampa_df,
        )
        mock_estela_vectorizado.assert_called_once()
        mock_vecdir_tj.assert_called_once()

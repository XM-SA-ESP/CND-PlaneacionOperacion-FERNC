import unittest
import pandas as pd
import pandas.testing as pdt
from xm_solarlib.location import Location

from utils.solar.funciones_dni_dhi import CalculoDniDhi


class TestCalculoDniDhi(unittest.TestCase):
    def setUp(self) -> None:
        data = "./tests/data/test_dataframe.parquet"
        self.df_pd = pd.read_parquet(data)
        self.calculo_dni_dhi_instancia = CalculoDniDhi()
        self.mock_series = pd.read_excel(
            "./tests/data/test_series_tiempo.xlsx", index_col=0
        )
        self.mock_solpos = pd.read_excel(
            "./tests/data/test_angulo_zenital.xlsx", index_col=0
        )
        self.mock_iext = pd.read_excel("./tests/data/test_iext.xlsx", index_col=0)
        self.mock_dni = pd.read_excel("./tests/data/test_series_dni.xlsx", index_col=0)
        self.mock_dni_dhi = pd.read_excel(
            "./tests/data/test_serie_dni_dhi.xlsx", index_col=0
        )
        self.mock_calculo_df = pd.read_excel(
            "./tests/data/test_calculo_df.xlsx", index_col=0
        )

        # Localizacion para tests
        self.localizacion = Location(4.604535, -74.066038, "America/Bogota", 2632.10)

    def test_obtener_localizacion(self):
        """
        Prueba del método obtener_localizacion de la clase CalculoDniDhiInstancia.

        Este método toma la latitud, longitud, zona horaria y altitud como parámetros.
        Llama al método obtener_localizacion de la clase CalculoDniDhiInstancia con estos parámetros
        y asigna el resultado a la variable actual_location.

        Luego verifica que la latitud, longitud, zona horaria y altitud de actual_location
        coincidan con los atributos respectivos del objeto self.localizacion.

        Esta prueba asegura que el método obtener_localizacion devuelve el objeto de ubicación esperado.

        Parámetros:
            latitude (float): La latitud de la ubicación.
            longitude (float): La longitud de la ubicación.
            tz (str): La zona horaria de la ubicación.
            altitude (float): La altitud de la ubicación.

        Retorna:
            None
        """
        latitude = 4.604535
        longitude = -74.066038
        tz = "America/Bogota"
        altitude = 2632.10

        actual_location = self.calculo_dni_dhi_instancia.obtener_localizacion(
            latitude, longitude, tz, altitude
        )

        self.assertEqual(actual_location.latitude, self.localizacion.latitude)
        self.assertEqual(actual_location.longitude, self.localizacion.longitude)
        self.assertEqual(actual_location.tz, self.localizacion.tz)
        self.assertEqual(actual_location.altitude, self.localizacion.altitude)

    def test_obtener_angulo_zenital(self):
        """
        Prueba del método obtener_angulo_zenital.

        Esta función prueba el método obtener_angulo_zenital de la clase CalculoDniDhi.
        Verifica que el método calcule correctamente el ángulo cenital para una ubicación y una serie de datos dadas.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None
        """

        series = self.mock_series

        resultado_esperado = self.mock_solpos

        # Invocacion del metodo __obtener_angulo_zenital
        resultado = self.calculo_dni_dhi_instancia.obtener_angulo_zenital(
            self.localizacion, series["series"]
        )

        # Index de resultado esperado en str. Convertir a datetime usando el resultado obtenido
        resultado_esperado.index = resultado.index

        # assert_frame_equal entre el resultado y el df esperado
        pdt.assert_frame_equal(resultado, resultado_esperado)

    # def test_obtener_irradiacion_extraterrestre(self):
    #     """
    #     Prueba la función obtener_irradiacion_extraterrestre.

    #     Parámetros:
    #         self: La instancia de la clase de prueba que contiene el método de prueba.

    #     Retorna:
    #         None
    #     """

    #     # Generar Serie de tiempo para el calculo
    #     mock_series = pd.date_range(start="1/1/2008", end="1/1/2010", freq="1h")

    #     # Leer archivo local iext con el resultado esperado
    #     resultado_esperado = pd.read_excel(
    #         "./tests/data/test_iext_local.xlsx",
    #         index_col=0,
    #         header=None,
    #         names=["iext"],
    #     )
    #     resultado_esperado = resultado_esperado[1:]

    #     # Invocacion del metodo __obtener_irradiacion_extraterrestre
    #     resultado = self.calculo_dni_dhi_instancia.obtener_irradiacion_extraterrestre(
    #         mock_series
    #     )

    #     # Convertir a Dataframe para la prueba
    #     resultado = pd.DataFrame(resultado, columns=["iext"])

    #     resultado_esperado.index = resultado.index

    #     # assert_frame_equal entre el resultado y el df esperado
    #     pdt.assert_series_equal(resultado["iext"], resultado_esperado["iext"])

    def test_obtener_dni(self):
        """
        Caso de prueba para el método `obtener_dni`.

        Este caso de prueba valida la funcionalidad del método `obtener_dni`.
        Se proporciona un DataFrame simulado con valores específicos y compara el
        resultado obtenido con el DataFrame esperado.

        Parámetros:
            self: La instancia de la clase de prueba.

        Retorna:
            None
        """
        mock_df = pd.DataFrame(
            {"zenith": [50, 100, 150], "GHI": [0.5, 0.6, 0.7]},
            index=pd.to_datetime(
                ["09:00", "12:00", "18:00"], format="%H:%M"
            ).tz_localize("America/Bogota"),
        )

        resultado_esperado = pd.DataFrame(
            {
                "dni": [0.0, 0.0, 0.0],
                "kt": [0.000549, 0.006510, 0.007595],
                "airmass": [1.552552, 0.0, 0.0],
            },
            index=pd.to_datetime(
                ["09:00", "12:00", "18:00"], format="%H:%M"
            ).tz_localize("America/Bogota"),
        )

        resultado = self.calculo_dni_dhi_instancia.obtener_dni(mock_df)

        # Se redondean los resultados a 4 decimales para hacer la prueba
        resultado = resultado.round(4)
        resultado_esperado = resultado_esperado.round(4)

        # assert_frame_equal entre el resultado y el df esperado
        pdt.assert_frame_equal(resultado, resultado_esperado)

    def test_obtener_dhi(self):
        """
        Prueba la funcionalidad del método `obtener_dhi`.

        Este método prueba la funcionalidad del método privado `obtener_dhi` en la clase
        `CalculoDniDhi`. Llama al método con los parámetros `series_dni` y `calc_df` proporcionados
        y compara el resultado con el DataFrame esperado `resultado_esperado`. La función
        `assert_frame_equal` se utiliza para realizar la comparación y generar un AssertionError
        si los dos DataFrames no son iguales.

        Parámetros:
            self: La instancia de la clase de prueba que contiene el método de prueba.

        Retorna:
            None
        """

        series_dni = self.mock_dni
        calc_df = self.mock_calculo_df

        resultado_esperado = self.mock_dni_dhi

        resultado = self.calculo_dni_dhi_instancia.obtener_dhi(series_dni, calc_df)

        # assert_frame_equal entre el resultado y el df esperado
        pdt.assert_frame_equal(resultado, resultado_esperado)

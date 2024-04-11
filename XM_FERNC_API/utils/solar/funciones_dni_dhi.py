import xm_solarlib
import polars as pl
from xm_solarlib.location import Location
from pandas.core.frame import DataFrame as Pandas_Dataframe

from utils.solar.calculos_polars import calculo_dhi
from utils.solar import data_constants

class CalculoDniDhi:
    def __init__(self) -> None:
        return

    def obtener_localizacion(
        self,
        latitude: float,
        longitude: float,
        tz: str,
        altitude: int,
    ) -> Location:
        """
        Crea y devuelve un objeto Location con la información de la ubicación proporcionada.

        Parámetros:
        - latitude: La latitud de la ubicación en grados decimales.
        - longitude: La longitud de la ubicación en grados decimales.
        - tz: La zona horaria de la ubicación, expresada como una cadena (por ejemplo, "America/New_York").
        - altitude: La altitud de la ubicación en metros sobre el nivel del mar.

        Retorno:
        - Location: Un objeto Location que representa la ubicación geográfica proporcionada.
        """
        location = Location(latitude, longitude, tz, altitude)
        return location

    def obtener_angulo_zenital(
        self, localizacion: Location, series: Pandas_Dataframe
    ) -> Pandas_Dataframe:
        """           
        Calcula y devuelve el ángulo zenital solar para una ubicación y serie de tiempo dadas.

        Parámetros:
        - localizacion: Un objeto Location que representa la ubicación geográfica.
        - series: Un DataFrame de pandas que contiene la serie de tiempo para la cual se calculará el ángulo zenital solar.

        Retorno:
        - Pandas_Dataframe: Un DataFrame de pandas que contiene la información de la posición solar, incluido el ángulo zenital.
        """
        posicion_solar = localizacion.get_solarposition(series)
        return posicion_solar

    def obtener_irradiacion_extraterrestre(
        self, series: Pandas_Dataframe
    ) -> Pandas_Dataframe:
        """
        Calcula y devuelve la irradiación extraterrestre para una serie de tiempo dada.

        Parámetros:
        - series: Un DataFrame de pandas que contiene la serie de tiempo para la cual se calculará la irradiación extraterrestre.

        Retorno:
        - Pandas_Dataframe: Un DataFrame de pandas que contiene la irradiación extraterrestre calculada.
        """

        iext = xm_solarlib.irradiance.get_extra_radiation(
            datetime_or_doy=series
        )

        return iext

    def obtener_dni(self, df: Pandas_Dataframe) -> Pandas_Dataframe:
        """
        Calcula y devuelve la radiación directa normalizada (DNI) a partir de la radiación global horizontal (GHI) y la serie de tiempo dada.

        Parámetros:
        - df: Un DataFrame de pandas que contiene la serie de tiempo con información de radiación global horizontal y otros parámetros.

        Retorno:
        - Pandas_Dataframe: Un DataFrame de pandas que contiene la radiación directa normalizada (DNI) calculada.
        """
        serie_dni = xm_solarlib.irradiance.disc(
            ghi=df.GHI,
            datetime_or_doy=df.index,
            solar_zenith=df.zenith,
            pressure=None,
        )
        serie_dni["airmass"] = serie_dni["airmass"].fillna(0.0)
        return serie_dni

    def obtener_dhi(
        self, serie_dni: Pandas_Dataframe, calculo_df: Pandas_Dataframe
    ) -> Pandas_Dataframe:
        """
        Calcula y devuelve la radiación difusa normalizada (DHI) a partir de la radiación directa normalizada (DNI) y otros parámetros.

        Parámetros:
        - serie_dni: Un DataFrame de pandas que contiene la serie de tiempo con información de radiación directa normalizada (DNI).
        - calculo_df: Un DataFrame de pandas que contiene la información necesaria para el cálculo de la radiación difusa normalizada (DHI).

        Retorno:
        - Pandas_Dataframe: Un DataFrame de pandas que contiene la radiación difusa normalizada (DHI) calculada.
        """

        serie_dni[data_constants.COLUMN_GHI] = calculo_df["GHI"]
        serie_dni["zenith"] = calculo_df["zenith"]

        local_df = pl.from_pandas(serie_dni)

        local_df = local_df.with_columns(
            [
                pl.struct([data_constants.COLUMN_GHI, "dni", "zenith"])
                .apply(lambda cols: calculo_dhi(list(cols.values())))
                .alias("dhi")
            ]
        )

        serie_dni["dhi"] = local_df["dhi"]
        del local_df

        serie_dni = serie_dni[["dni", "dhi", "kt", "zenith", data_constants.COLUMN_GHI, "airmass"]]

        # Filtrar dni y dhi a cero si el zenith es mayor a 87
        serie_dni.loc[serie_dni["zenith"] > 87, ["dni", "dhi"]] = 0

        # Filtrar dni y dhi a cero si dni <= 0 y dhi < 0
        mask = (serie_dni["dni"] <= 0) & (serie_dni["dhi"] < 0)
        serie_dni.loc[mask, ["dni", "dhi"]] = 0.0

        return serie_dni

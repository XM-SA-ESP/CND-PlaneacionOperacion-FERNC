import pandas as pd

from infraestructura.models.eolica.parametros import (
    JsonModelEolica,
    Aerogeneradores,
    CurvasDelFabricante,
)


class CorregirCurvas:
    def __init__(self) -> None:
        pass

    def corregir_curvas_con_torre(
        self, torres_dict, modelos_dict, aerogeneradores
    ) -> None:
        """
        Corrige las curvas de rendimiento del aerogenerador teniendo en cuenta la densidad del aire en la torre.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - torres_dict: Un diccionario que mapea identificadores de torres a objetos de torre que contienen datos relevantes.
        - modelos_dict: Un diccionario que mapea nombres de modelos de aerogeneradores a objetos que contienen características del modelo.
        - aerogeneradores: Un diccionario que mapea identificadores de aerogeneradores a objetos de aerogeneradores.

        Retorno:
        - None: Este método no devuelve ningún valor. Las correcciones se realizan directamente en las curvas de rendimiento de los aerogeneradores.
        """
        torres_calculadas = set()
        for aero in aerogeneradores.values():
            caracteristicas = modelos_dict[aero.modelo]
            den_nominal = caracteristicas.den_nominal
            v_nominal = caracteristicas.v_nominal
            v_max = caracteristicas.v_max
            v_diseno = self.__obtener_vel_diseno(caracteristicas)
            if aero.id_torre not in torres_calculadas:
                data_torre = torres_dict[aero.id_torre].dataframe
                den_promedio = self.obtener_promedio_densidad_buje(
                    data_torre["DenBuje"]
                )
                if den_nominal != den_promedio:
                    for curvas in caracteristicas.curvas_fabricante:
                        self.obtener_vp_vcth_corregida(
                            curvas,
                            den_nominal,
                            den_promedio,
                            v_max,
                            v_nominal,
                            v_diseno,
                        )
                torres_calculadas.add(aero.id_torre)

    def corregir_curvas_sin_torres(
        self, params: JsonModelEolica, df: pd.DataFrame
    ) -> None:
        """
        Corrige las curvas de rendimiento del aerogenerador sin tener en cuenta torres específicas.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - params: Un objeto JsonModelEolica que contiene parámetros de configuración para la modelización eólica.
        - df: Un DataFrame de pandas que contiene datos relevantes, especialmente la densidad del buje.

        Retorno:
        - None: Este método no devuelve ningún valor. Las correcciones se realizan directamente en las curvas de rendimiento de los aerogeneradores.
        """
        den_promedio = self.obtener_promedio_densidad_buje(df["DenBuje"])
        for modelo in params.ParametrosConfiguracion.Aerogeneradores:
            den_nominal = modelo.DensidadNominal
            v_nominal = modelo.VelocidadNominal
            v_max = modelo.VelocidadCorteSuperior
            v_diseno = self.__obtener_vel_diseno(modelo)
            if den_promedio != den_nominal:
                for curvas in modelo.CurvasDelFabricante:
                    self.obtener_vp_vcth_corregida(
                        curvas, den_nominal, den_promedio, v_max, v_nominal, v_diseno
                    )
                return
            else:
                return

    def obtener_promedio_densidad_buje(self, densidad_series: pd.Series) -> float:
        return densidad_series.mean()

    def obtener_vp_vcth_corregida(
        self,
        curvas: CurvasDelFabricante,
        den_nominal: float,
        den_promedio: float,
        v_max: float,
        v_nominal: float,
        v_diseno: float,
    ) -> None:
        """
        Corrige los valores de velocidad de potencia (VP) y velocidad de corte superior (VCTH) en las curvas del fabricante
        basándose en la densidad del aire nominal y el promedio de densidad del buje.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - curvas: Un objeto CurvasDelFabricante que contiene las curvas del fabricante, incluyendo la serie de velocidad.
        - den_nominal: Densidad del aire nominal según las especificaciones del modelo.
        - den_promedio: Promedio de densidad del buje calculado a partir de datos reales.
        - v_max: Velocidad máxima del aerogenerador según las especificaciones del modelo.
        - v_nominal: Velocidad nominal del aerogenerador según las especificaciones del modelo.
        - v_diseno: Velocidad de diseño del aerogenerador según las especificaciones del modelo.
        """
        v_fabricante = curvas.SerieVelocidad

        if 0 <= v_fabricante < v_diseno:
            m = 1 / 3
            vp_corregida = v_fabricante * ((den_nominal / den_promedio) ** m)
            coef_n = 1 / 8
            vcth_corregida = v_fabricante * ((den_nominal / den_promedio) ** coef_n)
            if vp_corregida > v_max:
                vp_corregida = v_max
            if vcth_corregida > v_max:
                vcth_corregida = v_max
            curvas.SerieVelocidad = vp_corregida
            curvas.SerieVcthCorregida = vcth_corregida

        elif v_diseno <= v_fabricante <= v_nominal:
            m = (1 / 3) + (
                (1 / 3) * ((v_fabricante - v_diseno) / (v_nominal - v_diseno))
            )
            vp_corregida = v_fabricante * ((den_nominal / den_promedio) ** m)

            coef_n = (1 / 8) + (
                ((1 / 3) - (1 / 8))
                * ((v_fabricante - v_diseno) / (v_nominal - v_diseno))
            )

            vcth_corregida = v_fabricante * ((den_nominal / den_promedio) ** coef_n)
            if vp_corregida > v_max:
                vp_corregida = v_max
            if vcth_corregida > v_max:
                vcth_corregida = v_max
            curvas.SerieVelocidad = vp_corregida
            curvas.SerieVcthCorregida = vcth_corregida

        else:
            m = 2 / 3
            vp_corregida = v_fabricante * ((den_nominal / den_promedio) ** m)
            coef_n = 1 / 3
            vcth_corregida = v_fabricante * ((den_nominal / den_promedio) ** coef_n)
            if vp_corregida > v_max:
                vp_corregida = v_max
            if vcth_corregida > v_max:
                vcth_corregida = v_max
            curvas.SerieVelocidad = vp_corregida
            curvas.SerieVcthCorregida = vcth_corregida


    def __obtener_vel_diseno(self, modelo: Aerogeneradores) -> tuple:
        """
        Obtiene la velocidad de diseño y la relación máxima entre potencia y velocidad de las curvas del fabricante.

        Parámetros:
        - self: Instancia de la clase que contiene el método.
        - modelo: Un objeto Aerogeneradores que contiene las curvas del fabricante y otros datos del modelo.

        Retorno:
        - tuple: Una tupla que contiene la velocidad de diseño y la relación máxima entre potencia y velocidad.
        """
        vel_diseno = 0
        relacion_max = 0
        if isinstance(modelo, Aerogeneradores):
            curvas = modelo.CurvasDelFabricante
        else:
            curvas = modelo.curvas_fabricante
        for curva in curvas:
            p_fabricante = curva.SeriePotencia
            v_fabricante = curva.SerieVelocidad
            v_diseno = p_fabricante / (v_fabricante**3)

            if relacion_max < v_diseno:
                relacion_max = v_diseno
                vel_diseno = v_fabricante

        return vel_diseno

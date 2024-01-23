from typing import Dict

from infraestructura.models.eolica.parametros import ParametrosTransversales


class AjustePotencia:
    """
    Clase que contiene los metodos para el ajuste de la potencia de los aerogeneradores.
    """
    def __init__(self) -> None:
        """
        Inicializa la clase AjustePotencia.
        """
        pass

    def ajuste_potencia_aerogeneradores(
        self,
        params_trans: ParametrosTransversales,
        aerogeneradores: Dict,
        modelos: Dict,
        ohm: float
    ) -> Dict:
        """
        Ajuste de la potencia de cada aerogenerador.

        Args:
            - params_trans (ParametrosTransversales): Objeto ParametrosTransversales provenientes del JSON.
            - aerogeneradores (Dict): Diccionario que contiene objetos Aerogenerador.
            - modelos (Dict): Diccionario que contiene objetos Modelo.
            - ohm (float): Resistencia promedio del cableado de las conexiones.
        Retorna:
            - aerogeneradores (Dict): Diccionario con objetos Aerogenerador con el campo df actualizado con
            una columna llamada 'PotenciaAjustada'.
        """
        v = params_trans.Voltaje
        kpc = params_trans.Kpc
        kt = params_trans.Kt
        kin = params_trans.Kin

        for aero in aerogeneradores.values():
            modelo = modelos[aero.modelo]
            den_nominal = modelo.den_nominal
            p_nominal = modelo.p_nominal

            aero.df["PotenciaAjustada"] = 0

            aero.df["PotenciaAjustada"] = aero.df.apply(
                lambda row: self.__obtener_pi_pc1(
                    row["Potencia"], den_nominal, row["DenBuje"]
                )
            , axis=1)
            aero.df["PotenciaAjustada"] = aero.df.apply(
                lambda row: self.__obtener_pi_pc2(row["PotenciaAjustada"], ohm, v, aero.dist_pcc)
            , axis=1)
            aero.df["PotenciaAjustada"] = aero.df.apply(
                lambda row: self.__obtener_pi_pc3(row["PotenciaAjustada"], kpc, kt, kin)
            , axis=1)

            aero.df["PotenciaAjustada"].loc[
                aero.df["PotenciaAjustada"] > p_nominal
            ] = p_nominal

        return aerogeneradores

    def __obtener_pi_pc1(self, p: float, den_nominal: float, den_buje: float) -> float:
        """
        Calculo de la serie de potencia ajustada de cada aerogenerador.

        Args:
            - p (float): Potencia del aerogenerador.
            - den_nominal (float): Densidad nominal.
            - den_buje (float): Densidad a la altura del buje del aerogenerador.
        Retorna:
            - pi_c1 (float): Potencia ajustada del aerogenerador.
        """
        pi_c1 = p * (den_nominal / den_buje)
        return pi_c1

    def __obtener_pi_pc2(
        self, pi_c1: float, ohm: float, voltaje: float, x_pcc: float
    ) -> float:
        """
        Ajuste de la potencia de cada aerogenerador por las perdidas del cableado electrico.

        Args:
            - pi_c1 (float): Potencia ajustada.
            - ohm (float): Promedio de la resistencia del cableado de las conexiones.
            - voltaje (float): Parametro voltaje.
            - x_pcc (float): Distancia en km del areogenerador al PCC.
        Retorna:
            - pi_c2 (float): Potencia ajustada por las perdidad del cableado electrico.
        """
        pi_c2 = ((pi_c1 * 1000) - (((pi_c1 / voltaje) ** 2) * ohm * x_pcc)) / 1000
        return pi_c2

    def __obtener_pi_pc3(
        self, pi_c2: float, kpc: float, kt: float, kin: float
    ) -> float:
        """
        Ajuste de la potencia por las perdidas de transmision hasta la frontera comercial.

        Args:
            - pi_c2 (float): Potencia ajustada por perdidas del cableado.
            - kpc (float): Coeficiente de perdida (Parametros transversales)
            - kt (float): Coeficiente de perdida (Parametros transversales)
            - kin (float): Coeficiente de perdida (Parametros transversales)
        - Retorna:
            - pi_c3 (float): Potencia ajustada por perdidas de transmision hasta la frontera comercial.
        """
        pi_c3 = pi_c2 * (1 - (kpc / 100)) * (1 - (kt / 100)) * (1 - (kin / 100))
        return pi_c3

from typing import Dict
import pandas as pd
import numpy as np
from infraestructura.models.eolica.parametros import JsonModelEolica

from utils.eolica.dataclasses_eolica import Aerogenerador
from utils.eolica.funciones_correccion_velocidad_parque_eolico import (
    CorreccionVelocidadParque,
)


class CalculoPotencia:
    def __init__(self) -> None:
        pass

    def potencia_planta_eolica(
        self, aerogeneradores: Dict[str, Aerogenerador], params: JsonModelEolica
    ) -> pd.Series:
        """
        :param aerogeneradores: Diccionario de Aerogenerador, donde cada uno tiene un DataFrame con una columna 'Potencia'.
        :param params: Instancia de JsonModelEolica que contiene parámetros transversales.
        :return: Serie de pandas con la suma de potencias ajustadas para cada índice de tiempo,
                 con el valor máximo limitado por Ppi para cada índice.
        """
        lista_potencias = []

        # Iterar sobre cada Aerogenerador para ajustar su potencia
        for aerogenerador in aerogeneradores.values():
            lista_potencias.append(aerogenerador.df["PotenciaAjustada"])

        # Sumar todas las potencias ajustadas a lo largo del eje 0 (verticalmente)
        potencia_total_ajustada = pd.concat(lista_potencias, axis=1).sum(axis=1)
        potencia_total_ajustada = potencia_total_ajustada * (
            1 - (params.ParametrosTransversales.Ihf / 100)
        )

        # Limitar el valor máximo de la potencia total ajustada a Ppi para cada índice
        potencia_total_ajustada = potencia_total_ajustada.clip(
            upper=params.ParametrosTransversales.Ppi
        )
    
        potencia_total_ajustada.name = "energia_kWh"

        return potencia_total_ajustada

    def interpolar_potencia(
        self, viento: float, curva_vel: np.array, curva_potencia: np.array
    ) -> float:
        """
        Interpola la potencia de un aerogenerador dado su velocidad del viento utilizando curvas de potencia y velocidad dadas.

        :param viento: La velocidad del viento para la cual se desea obtener la potencia.
        :param curva_vel: Un array de numpy con las velocidades de la curva del fabricante.
        :param curva_potencia: Un array de numpy con las potencias correspondientes a las velocidades de la curva del fabricante.
        :return: La potencia interpolada.
        """
        # Verificamos que los arrays de velocidad y potencia tengan el mismo tamaño
        if len(curva_vel) != len(curva_potencia):
            raise ValueError(
                "Los arrays de velocidad y potencia deben tener el mismo tamaño."
            )

        # Creamos la spline cúbica con los datos proporcionados
        """
        El parámetro k puede tomar valores enteros del 1 al 5:

        k=1 producirá una spline lineal (piezas lineales conectadas).
        k=2 creará una spline cuadrática (polinomios de segundo grado).
        k=3 (que es el que se utiliza aquí) genera una spline cúbica, que es la más común. 
            Las splines cúbicas son polinomios de tercer grado que se caracterizan por su suavidad 
            y son ampliamente utilizadas en la interpolación debido a su buen equilibrio entre 
            precisión y suavidad de la curva.
        k=4 y k=5 serían splines de grado cuártico y quíntico respectivamente, pero se utilizan 
        con menos frecuencia.
        La elección de k=3 para la spline cúbica es habitual porque ofrece un buen compromiso 
        entre flexibilidad de la curva y estabilidad numérica, y en muchas aplicaciones prácticas 
        ha demostrado ser suficientemente precisa. Además, las splines cúbicas tienen buenas 
        propiedades matemáticas; son suficientemente diferenciables (dos veces continuamente diferenciables) 
        lo que las hace adecuadas para modelar procesos físicos donde se necesitan calcular 
        derivadas, como en la dinámica de fluidos o la cinemática."""
        # tck = splrep(curva_vel, curva_potencia, k=3)
        # Calculamos la potencia interpolada para la velocidad del viento dada
        # potencia_interpolada = splev(viento, tck)
        potencia_interpolada = np.interp(viento, curva_vel, curva_potencia)
        return potencia_interpolada

    def calcular_potencia_aerogeneradores(self, aerogeneradores: Dict, modelos: Dict):
        for id_aero, aero in aerogeneradores.items():
            if isinstance(aero, Aerogenerador):
                modelo = modelos[aero.modelo]
                # Interpolamos y aplicamos las condiciones de velocidad y temperatura a cada fila del DataFrame
                (
                    curva_vel,
                    curva_potencia,
                ) = CorreccionVelocidadParque.obtener_curvas_potencia_velocidad(
                    modelo=modelo
                )
                aero.df["Potencia"] = aero.df.apply(
                    lambda row: self.interpolar_potencia(
                        viento=row["VelocidadEstela"],
                        curva_potencia=curva_potencia,
                        curva_vel=curva_vel,
                    )
                    if modelo.v_min <= row["VelocidadEstela"] <= modelo.v_max
                    and modelo.t_min <= row["Ta"] <= modelo.t_max
                    else 0,
                    axis=1,
                )
        return aerogeneradores

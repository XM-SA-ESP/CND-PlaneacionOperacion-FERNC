from enum import Enum


class MensajesSolar:
    """Enum para mensajes relacionados con calculos solar."""

    class Estado(Enum):
        DNI_DHI = "Ejecutando el modelo de descomposición - Cálculo de DNI y DHI"
        POA = "Ejecutando el modelo de transposición - Cálculo de la POA."
        CIRCUITO_EQUIVALENTE = (
            "Calculando los parámetros y la solución del circuito equivalente."
        )
        ENERGIA_DC_AC = "Calculando la producción en DC / AC."
        
        AJUSTANDO_ENERGIA = (
            "Ajustando la producción con las pérdidas y calculando la energía."
        )
        ENFICC = "Calculando ENFICC."

    class Error(Enum):
        DNI_DHI = "Error en el cálculo de la irradiancia difusa y directa (DHI-DNI). Verifique la serie de Irradiación Global Horizontal (GHI)."
        POA = "Error en el cálculo de la irradiancia en el plano del arreglo (POA). Verifique la serie de Irradiación Global Horizontal (GHI) y la bifacialidad, en caso de que aplique."
        CIRCUITO_EQUIVALENTE_PARAMETROS = "Error en el cálculo de los parámetros del circuito equivalente. Verifique los parámetros asociados a los paneles fotovoltaicos."
        CIRCUITO_EQUIVALENTE_SOLUCION = "Error en la solución del circuito equivalente. Verifique los parámetros asociados a los paneles fotovoltaicos."
        ENERGIA_DC = "Error en el cálculo de la producción en DC. Verifique los parámetros asociados a la configuración de la planta y los paneles fotovoltaicos."
        ENERGIA_AC = "Error en el cálculo de la producción en AC. Verifique los parámetros asociados a los inversores."
        CURVAS = "Error en el proceso de cálculo de la conversión DC-AC. Verifique los parámetros asociados a las curvas PDC vs PAC y los parámetros de los inversores."
        ENFICC = "Error en el calculo de la ENFICC."

class MensajesEolica():
    """Enum para mensajes relacionados con calculos eolica."""

    class Estado(Enum):
        VELOCIDAD_VIENTO = "Calculando velocidad del viento."
        ORDENAMIENTO = "Calculando el ordenamiento de los aerogeneradores según la dirección predominante del viento."
        PARQUES = "Ejecutando proceso de corrección de la velocidad por efecto de grandes parques."
        ESTELA = "Calculando velocidad del viento perturbada por efecto de estela."
        POTENCIA = "Calculando la producción energética del parque eólico."
        CURVAS = "Calculando curvas."
        CORRECCION_PARQUES = "Correccion por grandes parques."
        CORRECCION_ESTELA = "Correccion por efecto estela"
    class Error(Enum):
        ASIGNAR_TORRES_A_EROGENERADOR = "Error en la asignación de los datos a cada aerogenerador. Verifique la ubicación de los aerogeneradores y el radio de representatividad."
        ORDENAMIENTO = "Error en el cálculo del ordenamiento. Verifique los parámetros de los aerogeneradores y la serie de dirección del viento."
        PARQUES = "Error en la corrección del viento por efecto de grandes parques. Verifique los parámetros de los aerogeneradores."
        ESTELA = "Error en el ajuste de la velocidad por efecto estela. Verifique los parámetros de los aerogeneradores."
        POTENCIA = "Error en el cálculo y ajuste de la potencia. Verifique los parámetros de los aerogeneradores."
        CURVAS = "Error en el cálculo de la potencia. Verifique las curvas del fabricante ingresadas."
        H_PRIMA = "Error en el calculo de la altura de la capa limite. Verifique los parámetros de los aerogeneradores."
        RADIO_ESTELA = "Error en el calculo de la estela. Verifique los parámetros de los aerogeneradores."
        SPLINE_CUBICO = "Error en la interpolacion del coeficiente de empuje. Verifique los parámetros correspondientes a las curvas del fabricante."
        DISTANCIA_ESTELA_ROTOR = "Error en el calculo de la distancia de la estela del aerogenerador. Verifique los parámetros de los aerogeneradores."
        XARRAY = "Error en la estructura de xarray comuniquese con el administrador."
        ATMOSFERA_DATAFRAME = "Se identificaron valores de presión atmosférica elevados en la serie. Verifique la serie ingresada para esta variable."
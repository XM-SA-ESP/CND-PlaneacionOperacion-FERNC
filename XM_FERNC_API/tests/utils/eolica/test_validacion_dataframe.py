import pandas as pd
import pytest
from XM_FERNC_API.utils.eolica.validaciones_dataframe import validar_presion_atmosferica  # Asegúrate de importar correctamente tu función y módulos
from XM_FERNC_API.utils.mensaje_constantes import MensajesEolica
from XM_FERNC_API.utils.manipulador_excepciones import CalculoExcepcion

def test_validar_presion_atmosferica_excepcion():
    data = {
        'PresionAtmosferica': [3100, 2900, 3050]
    }
    df = pd.DataFrame(data)

    with pytest.raises(CalculoExcepcion) as excinfo:
        validar_presion_atmosferica(df)

    assert str(excinfo.value.error) == "Valor no permitido para presión atmosférica en df"

    assert excinfo.value.tarea == "Validando Información"

    assert excinfo.value.mensaje == MensajesEolica.Error.ATMOSFERA_DATAFRAME.value
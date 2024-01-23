import polars as pl

import json
from main import app
from unittest.mock import patch
from fastapi.testclient import TestClient

client = TestClient(app)

# Cargar archivo con json data para el test
with open("./tests/data/test_json_data_eolica.json", "r") as file:
    test_json = json.load(file)


@patch("dominio.servicio.eolica.servicio_eolicas.ServicioEolicas.ejecutar_calculos")
def test_realizar_calculo_eolicas(mock_ejecutar_calculos):
    """
    Test para el endpoint /realizar_calculo_eolicas.
    Crea un Polars Dataframe mock.
    Parchea la funcion mock_ejecutar_calculos de ServicioEolicas y usa el dataframe mock como respuesta esperada.
    La funcion hace un POST request al /realizar_calculo_eolicas endpoint con el test_json payload. Asegura que la respuesta es un status 200.

    Esta funcion sirve como test case para el endpoint /realizar_calculo_eolicas, verificando su comportamiento.
    
    Parametros:
        None
    
    Retorna:
        None
    """
    mock_ejecutar_calculos.return_value = True

    response = client.post("/realizar_calculo_eolicas", json=test_json)

    assert response.status_code == 200

    mock_ejecutar_calculos.assert_called_once()

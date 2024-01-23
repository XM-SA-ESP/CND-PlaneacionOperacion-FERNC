import json
import polars as pl
from infraestructura.models.solar.parametros import JsonModelSolar

from main import app
from unittest.mock import patch
from fastapi.testclient import TestClient

client = TestClient(app)


# Writing the JSON data to a file
with open("./tests/data/test_json_data.json", "r") as file:
    test_json = json.load(file)


@patch("dominio.servicio.solar.servicio_solares.ServicioSolar.generar_dataframe")
@patch("dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculos")
def test_realizar_calculo_solares(
    mock_ejecutar_calculos, mock_generar_dataframe
):
    """
    Test para el endpoint /realizar_calculo_eolicas.
    Crea un Polars Dataframe mock.
    Parchea las funciones generar_dataframe y ejecutar_calculo_dni_dhi de ServicioSolar y usa el dataframe mock como respuesta esperada.
    La funcion hace un POST request al /realizar_calculo_solares endpoint con el test_json payload. Asegura que la respuesta es un status 200.

    Esta funcion sirve como test case para el endpoint /realizar_calculo_solares, verificando su comportamiento.

    Parametros:
        None

    Retorna:
        None
    """
    mock_df = pl.read_parquet("./tests/data/test_dataframe.parquet")
    mock_generar_dataframe.return_value = mock_df

    response = client.post("/realizar_calculo_solares", json=test_json)

    assert response.status_code == 200

    mock_generar_dataframe.assert_called_once_with("test_file.parquet")
    mock_ejecutar_calculos.assert_called_once()


@patch("dominio.servicio.solar.servicio_solares.ServicioSolar.generar_dataframe")
def test_realizar_calculo_solares_df_empty(mock_generar_dataframe):

    mock_df = pl.DataFrame()

    mock_generar_dataframe.return_value = mock_df

    response = client.post("/realizar_calculo_solares", json=test_json)

    assert response.status_code == 404

    mock_generar_dataframe.assert_called_once_with("test_file.parquet")


@patch("dominio.servicio.solar.servicio_solares.ServicioSolar.generar_dataframe")
@patch("dominio.servicio.solar.servicio_solares.ServicioSolar.ejecutar_calculos")
def test_realizar_calculo_solares_response_none(mock_ejecutar_calculos, mock_generar_dataframe):

    mock_df = pl.read_parquet("./tests/data/test_dataframe.parquet")
    mock_generar_dataframe.return_value = mock_df
    mock_ejecutar_calculos.return_value = None

    response = client.post("/realizar_calculo_solares", json=test_json)

    assert response.status_code == 404

    mock_generar_dataframe.assert_called_once_with("test_file.parquet")
    mock_ejecutar_calculos.assert_called_once()

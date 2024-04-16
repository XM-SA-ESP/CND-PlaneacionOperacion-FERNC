# Introduction 
Este microservicio incluye los endpoints esenciales para obtener información para el cálculo de la **ENFICC** y la **EDA**. Estos endpoints son fundamentales para iniciar y gestionar el cálculo.

# Proposito/Objetivo.: 
Proyecto requerido para las resoluciones CREG 101 006 de 2023 para plantas eólicas y CREG 101 007 de 2023 para plantas solares fotovoltaicas, donde se define la metodología para determinar la energía firme para el cargo por confiabilidad y donde se regulan otras disposiciones.

#Funcionalidades/Features:
1. Calcular ENFICC para plantas solares.
2. Calcular EDA para plantas eólicas.
3. Producción energetida horaria para plantas solares y eólicas.

# Forma de uso/Ejemplos.
1. **Descargar el Repositorio:** Clone el repositorio a su máquina local.
2. **Abrir el Proyecto:** Abra el proyecto utilizando su IDE preferido, como por ejemplos Visual Studio Code.
3. **Compilar y Restaurar Paquetes:** Ejecuta la compilación del proyecto para asegurarte de que todos los archivos necesarios estén en su lugar, usando los comandos (pip install -r .\requirements.txt) y (run .\main.py) ubicado en la carpeta ".\XM_FERNC_API".
4. **Configurar Variables de Entorno:** las variables de encontro se encuentran en el archivo **.env**
5. **Instalar libreria adicional:** Configura la biblioteca SolarLib en tu proyecto, ya que es necesaria para ejecutar el modelo solar de manera efectiva [Descargar código fuente](https://github.com/XM-SA-ESP/CND-PlaneacionOperacion-SOLARLIB).
6. **Ejemplos de uso:** en modo desarrollo, la aplicación se suscribe a una cola de mensajeria que podra ser configurada por usted en un service bus y la estructura mensaje debe corresponder al siguiente ejemplo:

**Ejemplo modelo Solar:**
Valores disponibles para las siguientes propiedades:
- ParametrosTransversales.ZonaHoraria: "America/Bogota"
- EstructuraYConfiguracion.CantidadPanelConectados.Racking.Value: open_rack, close_mount y insulated_back
- ParametrosConfiguracion.GrupoInversores[x].ParametrosModulo.Tecnologia.Value: open_rack, close_mount y insulated_back

- El archivo Parquet debe ser almacenado en el repositorio de Blob Storage o localmente. Si deseas ejecutar el código localmente, ajusta el código para que pueda leer un archivo Parquet desde una ruta "df = pl.read_parquet(self.archivo_blob)". Puedes encontrar la plantilla xlsx correspondiente en la aplicación web y este debera ser convertido a parquet.
```json
{
	"CuerpoMensaje": {
		"ParametrosTransversales": {
			"ZonaHoraria": "America/Bogota",
			"Altitud": 423.0,
			"Albedo": 0.2,
			"L": 14.6,
			"Cen": 10.0,
			"Ihf": 3.0,
			"InformacionMedida": true,
			"Kin": 0.79,
			"Kpc": 0.66,
			"Kt": 0.61,
			"Latitud": 3.34,
			"Longitud": -73.87,
			"NombrePlanta": "{Nombre planta solar}",
			"Ppi": 10000000.0
		},
		"ParametrosConfiguracion": {
			"GrupoInversores": [
				{
					"ParametrosInversor": {
						"NInv": 49,
						"PACnocturnoW": 3.3,
						"PACnominal": 200000.0,
						"PDCarranque": 2025.07,
						"PDCnominal": 202507.04,
						"PowerAc": [
							84439.3,
							168868.3,
							337737.8,
							506607.4,
							844351.2,
							1266528.0,
							1688702.5,
							84439.6,
							168873.3,
							337739.3,
							508001.6,
							844347.6,
							1266525.2,
							1688695.9,
							84437.8,
							168865.3,
							337742.1,
							506606.0,
							844349.4,
							1266529.0,
							1688703.5
						],
						"PowerDc": [
							87520.0,
							172720.0,
							343090.0,
							513280.0,
							854520.0,
							1282560.0,
							1712680.0,
							88160.0,
							173310.0,
							343860.0,
							515790.0,
							856510.0,
							1285160.0,
							1715980.0,
							89060.0,
							174070.0,
							344670.0,
							515210.0,
							857730.0,
							1286600.0,
							1716860.0
						],
						"ReferenciaInversor": "Huawei_Technologies_SUN...",
						"VDCnominal": 1174.0
					},
					"ParametrosModulo": {
						"AlphaSc": 0.05,
						"AltoFilaPaneles": 2.38,
						"AnchoFilaPaneles": 1.3,
						"BetaOc": -0.26,
						"Bifacial": true,
						"Bifacialidad": 0.7,
						"GammaPmp": -0.34,
						"Impstc": 17.2,
						"Iscstc": 18.43,
						"Ns": 66,
						"Pnominalstc": 655.0,
						"Psi": 10.0,
						"ReferenciaModulo": "JAM72D30_565_GB_1500V",
						"Tecnologia": {
							"Value": "monosi"
						},
						"Tnoct": 45.0,
						"Vmpstc": 38.1,
						"Vocstc": 45.2
					},
					"EstructuraYConfiguracion": {
						"CantidadPanelConectados": [
							{
								"CantidadParalero": 5,
								"CantidadSerie": 32,
								"Id": 1,
								"OAzimutal": 180.0,
								"OElevacion": 0.0,
								"OMax": 55.0,
								"Racking": {
									"Value": "open_rack"
								}
							},
							{
								"CantidadParalero": 5,
								"CantidadSerie": 32,
								"Id": 2,
								"OAzimutal": 180.0,
								"OElevacion": 0.0,
								"OMax": 55.0,
								"Racking": {
									"Value": "open_rack"
								}
							},
							{
								"CantidadParalero": 4,
								"CantidadSerie": 32,
								"Id": 3,
								"OAzimutal": 180.0,
								"OElevacion": 0.0,
								"OMax": 55.0,
								"Racking": {
									"Value": "open_rack"
								}
							}
						],
						"EstructuraPlantaConSeguidores": true,
						"NSubarrays": 3
					}
				}
			]
		},
		"ArchivoSeries": {
			"Nombre": "archivo_serie.parquet"
		},
		"IdConexionWs": "",
		"IdTransaccion": "",
		"IdAplicacion": ""
	},
	"TipoMensaje": 0 //Solar
}
```

**Ejemplo modelo Eólico**
- El archivo Parquet debe ser almacenado en el repositorio de Blob Storage o localmente. Si deseas ejecutar el código localmente, ajusta el código para que pueda leer un archivo Parquet desde una ruta "df = pl.read_parquet(self.archivo_blob)". Puedes encontrar la plantilla xlsx correspondiente en la aplicación web y este debera ser convertido a parquet.
```json
{
	"CuerpoMensaje": {
		"IdConexionWs": "",
		"ParametrosTransversales": {
			"NombrePlanta": "Nombre planta eólica",
			"Cen": 120,
			"Ihf": 0,
			"Ppi": 100000000,
			"InformacionMedida": true,
			"Offshore": true,
			"Kpc": 0,
			"Kt": 0,
			"Kin": 0,
			"Latitud": 12.239873,
			"Longitud": -71.250362,
			"Elevacion": 32,
			"Voltaje": 36
		},
		"ParametrosConfiguracion": {
			"SistemasDeMedicion": [
				{
					"IdentificadorTorre": "Torre 1",
					"Latitud": 12.235873,
					"Longitud": -71.255362,
					"Elevacion": 0,
					"RadioRepresentatividad": 10,
					"CantidadAnemometro": 1,
					"ConfiguracionAnemometro": [
						{
							"Anemometro": 1,
							"AlturaAnemometro": 98
						}
					],
					"MostrarMarcadorPrevio": false,
					"ArchivoSeriesRelacionado": "series_eolicas.parquet"
				}
			],
			"Aerogeneradores": [
				{
					"ModeloAerogenerador": "E92/2.3MW",
					"AlturaBuje": 98,
					"DiametroRotor": 92,
					"PotenciaNominal": 2350,
					"VelocidadNominal": 14,
					"DensidadNominal": 1.23,
					"VelocidadCorteInferior": 2,
					"VelocidadCorteSuperior": 25,
					"TemperaturaAmbienteMinima": -10,
					"TemperaturaAmbienteMaxima": 45,
					"CurvasDelFabricante": [
						{
							"SerieVelocidad": 1,
							"SeriePotencia": 0,
							"SerieCoeficiente": 0
						},
						{
							"SerieVelocidad": 2,
							"SeriePotencia": 3.6,
							"SerieCoeficiente": 1
						},
						{
							"SerieVelocidad": 3,
							"SeriePotencia": 29.9,
							"SerieCoeficiente": 0.95
						},
						{
							"SerieVelocidad": 4,
							"SeriePotencia": 98.2,
							"SerieCoeficiente": 0.88
						},
						{
							"SerieVelocidad": 5,
							"SeriePotencia": 208.3,
							"SerieCoeficiente": 0.87
						},
						{
							"SerieVelocidad": 6,
							"SeriePotencia": 384.3,
							"SerieCoeficiente": 0.87
						},
						{
							"SerieVelocidad": 7,
							"SeriePotencia": 637,
							"SerieCoeficiente": 0.87
						},
						{
							"SerieVelocidad": 8,
							"SeriePotencia": 975,
							"SerieCoeficiente": 0.83
						},
						{
							"SerieVelocidad": 9,
							"SeriePotencia": 1403.6,
							"SerieCoeficiente": 0.77
						},
						{
							"SerieVelocidad": 10,
							"SeriePotencia": 1817.8,
							"SerieCoeficiente": 0.71
						},
						{
							"SerieVelocidad": 11,
							"SeriePotencia": 2088.7,
							"SerieCoeficiente": 0.67
						},
						{
							"SerieVelocidad": 12,
							"SeriePotencia": 2237,
							"SerieCoeficiente": 0.5
						},
						{
							"SerieVelocidad": 13,
							"SeriePotencia": 2300,
							"SerieCoeficiente": 0.37
						},
						{
							"SerieVelocidad": 14,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.29
						},
						{
							"SerieVelocidad": 15,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.23
						},
						{
							"SerieVelocidad": 16,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.19
						},
						{
							"SerieVelocidad": 17,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.16
						},
						{
							"SerieVelocidad": 18,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.13
						},
						{
							"SerieVelocidad": 19,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.11
						},
						{
							"SerieVelocidad": 20,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.1
						},
						{
							"SerieVelocidad": 21,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.09
						},
						{
							"SerieVelocidad": 22,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.08
						},
						{
							"SerieVelocidad": 23,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.07
						},
						{
							"SerieVelocidad": 24,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.06
						},
						{
							"SerieVelocidad": 25,
							"SeriePotencia": 2350,
							"SerieCoeficiente": 0.06
						}
					],
					"CantidadAerogeneradores": 50,
					"EspecificacionesEspacialesAerogeneradores": [
						{
							"Aerogenerador": 1,
							"Latitud": 12.29263,
							"Longitud": -71.226417,
							"Elevacion": 1,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 2,
							"Latitud": 12.287679,
							"Longitud": -71.226417,
							"Elevacion": 2,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 3,
							"Latitud": 12.282725,
							"Longitud": -71.226417,
							"Elevacion": 4,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 4,
							"Latitud": 12.27777,
							"Longitud": -71.226417,
							"Elevacion": 4,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 5,
							"Latitud": 12.272817,
							"Longitud": -71.226417,
							"Elevacion": 6,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 6,
							"Latitud": 12.267863,
							"Longitud": -71.226417,
							"Elevacion": 10,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 7,
							"Latitud": 12.262901,
							"Longitud": -71.226417,
							"Elevacion": 12,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 8,
							"Latitud": 12.257938,
							"Longitud": -71.226417,
							"Elevacion": 12,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 9,
							"Latitud": 12.252977,
							"Longitud": -71.226417,
							"Elevacion": 17,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 10,
							"Latitud": 12.248019,
							"Longitud": -71.226417,
							"Elevacion": 19,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 11,
							"Latitud": 12.29263,
							"Longitud": -71.239005,
							"Elevacion": 9,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 12,
							"Latitud": 12.287679,
							"Longitud": -71.239005,
							"Elevacion": 10,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 13,
							"Latitud": 12.282725,
							"Longitud": -71.239005,
							"Elevacion": 11,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 14,
							"Latitud": 12.27777,
							"Longitud": -71.239005,
							"Elevacion": 14,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 15,
							"Latitud": 12.272817,
							"Longitud": -71.239005,
							"Elevacion": 17,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 16,
							"Latitud": 12.267863,
							"Longitud": -71.239005,
							"Elevacion": 17,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 17,
							"Latitud": 12.2629,
							"Longitud": -71.239005,
							"Elevacion": 14,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 18,
							"Latitud": 12.257938,
							"Longitud": -71.239005,
							"Elevacion": 15,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 19,
							"Latitud": 12.252977,
							"Longitud": -71.239005,
							"Elevacion": 21,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 20,
							"Latitud": 12.248019,
							"Longitud": -71.239005,
							"Elevacion": 21,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 21,
							"Latitud": 12.29263,
							"Longitud": -71.251625,
							"Elevacion": 14,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 22,
							"Latitud": 12.287679,
							"Longitud": -71.251625,
							"Elevacion": 15,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 23,
							"Latitud": 12.282725,
							"Longitud": -71.251625,
							"Elevacion": 15,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 24,
							"Latitud": 12.27777,
							"Longitud": -71.251625,
							"Elevacion": 18,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 25,
							"Latitud": 12.272817,
							"Longitud": -71.251625,
							"Elevacion": 21,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 26,
							"Latitud": 12.267863,
							"Longitud": -71.251625,
							"Elevacion": 23,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 27,
							"Latitud": 12.262901,
							"Longitud": -71.251625,
							"Elevacion": 20,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 28,
							"Latitud": 12.257938,
							"Longitud": -71.25162,
							"Elevacion": 20,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 29,
							"Latitud": 12.252977,
							"Longitud": -71.251625,
							"Elevacion": 27,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 30,
							"Latitud": 12.248019,
							"Longitud": -71.251625,
							"Elevacion": 30,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 31,
							"Latitud": 12.29263,
							"Longitud": -71.264217,
							"Elevacion": 13,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 32,
							"Latitud": 12.287679,
							"Longitud": -71.264217,
							"Elevacion": 12,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 33,
							"Latitud": 12.282725,
							"Longitud": -71.264217,
							"Elevacion": 18,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 34,
							"Latitud": 12.27777,
							"Longitud": -71.264217,
							"Elevacion": 22,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 35,
							"Latitud": 12.272817,
							"Longitud": -71.264217,
							"Elevacion": 25,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 36,
							"Latitud": 12.267863,
							"Longitud": -71.264217,
							"Elevacion": 28,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 37,
							"Latitud": 12.262901,
							"Longitud": -71.264217,
							"Elevacion": 31,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 38,
							"Latitud": 12.257938,
							"Longitud": -71.264217,
							"Elevacion": 32,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 39,
							"Latitud": 12.252977,
							"Longitud": -71.264217,
							"Elevacion": 32,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 40,
							"Latitud": 12.248019,
							"Longitud": -71.264217,
							"Elevacion": 34,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 41,
							"Latitud": 12.29263,
							"Longitud": -71.276829,
							"Elevacion": 15,
							"MedicionAsociada": {
								"Label": "Torre 1",
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 42,
							"Latitud": 12.287679,
							"Longitud": -71.276829,
							"Elevacion": 8,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 43,
							"Latitud": 12.282725,
							"Longitud": -71.276829,
							"Elevacion": 9,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 44,
							"Latitud": 12.27777,
							"Longitud": -71.276829,
							"Elevacion": 11,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 45,
							"Latitud": 12.272817,
							"Longitud": -71.276829,
							"Elevacion": 12,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 46,
							"Latitud": 12.267863,
							"Longitud": -71.276829,
							"Elevacion": 18,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 47,
							"Latitud": 12.262901,
							"Longitud": -71.276829,
							"Elevacion": 20,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 48,
							"Latitud": 12.257938,
							"Longitud": -71.276829,
							"Elevacion": 25,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 49,
							"Latitud": 12.252977,
							"Longitud": -71.276829,
							"Elevacion": 31,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						},
						{
							"Aerogenerador": 50,
							"Latitud": 12.248019,
							"Longitud": -71.276829,
							"Elevacion": 28,
							"MedicionAsociada": {
								"Value": "Torre 1"
							}
						}
					]
				}
			],
			"ParametroConexion": [
				{
					"Conexion": 1,
					"CantidadAerogeneradoresConexion": 11,
					"Resistencia": 0.2,
					"ConexionAerogenerador": [
						{
							"OrdenConexion": 1,
							"IdentificadorAerogenerador": 1
						},
						{
							"OrdenConexion": 2,
							"IdentificadorAerogenerador": 2
						},
						{
							"OrdenConexion": 3,
							"IdentificadorAerogenerador": 3
						},
						{
							"OrdenConexion": 4,
							"IdentificadorAerogenerador": 4
						},
						{
							"OrdenConexion": 5,
							"IdentificadorAerogenerador": 5
						},
						{
							"OrdenConexion": 6,
							"IdentificadorAerogenerador": 6
						},
						{
							"OrdenConexion": 7,
							"IdentificadorAerogenerador": 7
						},
						{
							"OrdenConexion": 8,
							"IdentificadorAerogenerador": 8
						},
						{
							"OrdenConexion": 9,
							"IdentificadorAerogenerador": 9
						},
						{
							"OrdenConexion": 10,
							"IdentificadorAerogenerador": 10
						},
						{
							"OrdenConexion": 11,
							"IdentificadorAerogenerador": 20
						}
					]
				},
				{
					"Conexion": 2,
					"CantidadAerogeneradoresConexion": 10,
					"Resistencia": 0.2,
					"ConexionAerogenerador": [
						{
							"OrdenConexion": 1,
							"IdentificadorAerogenerador": 11
						},
						{
							"OrdenConexion": 2,
							"IdentificadorAerogenerador": 12
						},
						{
							"OrdenConexion": 3,
							"IdentificadorAerogenerador": 13
						},
						{
							"OrdenConexion": 4,
							"IdentificadorAerogenerador": 14
						},
						{
							"OrdenConexion": 5,
							"IdentificadorAerogenerador": 15
						},
						{
							"OrdenConexion": 6,
							"IdentificadorAerogenerador": 16
						},
						{
							"OrdenConexion": 7,
							"IdentificadorAerogenerador": 17
						},
						{
							"OrdenConexion": 8,
							"IdentificadorAerogenerador": 18
						},
						{
							"OrdenConexion": 9,
							"IdentificadorAerogenerador": 19
						},
						{
							"OrdenConexion": 10,
							"IdentificadorAerogenerador": 20
						}
					]
				},
				{
					"Conexion": 3,
					"CantidadAerogeneradoresConexion": 10,
					"Resistencia": 0.2,
					"ConexionAerogenerador": [
						{
							"OrdenConexion": 1,
							"IdentificadorAerogenerador": 21
						},
						{
							"OrdenConexion": 2,
							"IdentificadorAerogenerador": 22
						},
						{
							"OrdenConexion": 3,
							"IdentificadorAerogenerador": 23
						},
						{
							"OrdenConexion": 4,
							"IdentificadorAerogenerador": 24
						},
						{
							"OrdenConexion": 5,
							"IdentificadorAerogenerador": 25
						},
						{
							"OrdenConexion": 6,
							"IdentificadorAerogenerador": 26
						},
						{
							"OrdenConexion": 7,
							"IdentificadorAerogenerador": 27
						},
						{
							"OrdenConexion": 8,
							"IdentificadorAerogenerador": 28
						},
						{
							"OrdenConexion": 9,
							"IdentificadorAerogenerador": 29
						},
						{
							"OrdenConexion": 10,
							"IdentificadorAerogenerador": 30
						}
					]
				},
				{
					"Conexion": 4,
					"CantidadAerogeneradoresConexion": 11,
					"Resistencia": 0.2,
					"ConexionAerogenerador": [
						{
							"OrdenConexion": 1,
							"IdentificadorAerogenerador": 31
						},
						{
							"OrdenConexion": 2,
							"IdentificadorAerogenerador": 32
						},
						{
							"OrdenConexion": 3,
							"IdentificadorAerogenerador": 33
						},
						{
							"OrdenConexion": 4,
							"IdentificadorAerogenerador": 34
						},
						{
							"OrdenConexion": 5,
							"IdentificadorAerogenerador": 35
						},
						{
							"OrdenConexion": 6,
							"IdentificadorAerogenerador": 36
						},
						{
							"OrdenConexion": 7,
							"IdentificadorAerogenerador": 37
						},
						{
							"OrdenConexion": 8,
							"IdentificadorAerogenerador": 38
						},
						{
							"OrdenConexion": 9,
							"IdentificadorAerogenerador": 39
						},
						{
							"OrdenConexion": 10,
							"IdentificadorAerogenerador": 40
						},
						{
							"OrdenConexion": 11,
							"IdentificadorAerogenerador": 30
						}
					]
				},
				{
					"Conexion": 5,
					"CantidadAerogeneradoresConexion": 12,
					"Resistencia": 0.2,
					"ConexionAerogenerador": [
						{
							"OrdenConexion": 1,
							"IdentificadorAerogenerador": 41
						},
						{
							"OrdenConexion": 2,
							"IdentificadorAerogenerador": 42
						},
						{
							"OrdenConexion": 3,
							"IdentificadorAerogenerador": 43
						},
						{
							"OrdenConexion": 4,
							"IdentificadorAerogenerador": 44
						},
						{
							"OrdenConexion": 5,
							"IdentificadorAerogenerador": 45
						},
						{
							"OrdenConexion": 6,
							"IdentificadorAerogenerador": 46
						},
						{
							"OrdenConexion": 7,
							"IdentificadorAerogenerador": 47
						},
						{
							"OrdenConexion": 8,
							"IdentificadorAerogenerador": 48
						},
						{
							"OrdenConexion": 9,
							"IdentificadorAerogenerador": 49
						},
						{
							"OrdenConexion": 10,
							"IdentificadorAerogenerador": 50
						},
						{
							"OrdenConexion": 11,
							"IdentificadorAerogenerador": 40
						},
						{
							"OrdenConexion": 12,
							"IdentificadorAerogenerador": 30
						}
					]
				}
			]
		},
		"ArchivoSeries": {
			"Nombre": "",
			"ArchivoBase64": ""
		}
	},
	"TipoMensaje": 1 //Eólica
}
```
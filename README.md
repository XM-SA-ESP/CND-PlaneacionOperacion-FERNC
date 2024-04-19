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
6. **Ejemplos de uso:** en modo desarrollo, la aplicación se suscribe a una cola de mensajeria que podra ser configurada por usted en un service bus y la estructura del mensaje debe corresponder a los siguientes ejemplos:
Para ambos JSON, existe una propiedad denominada 'TipoMensaje'. Esta propiedad se emplea para identificar el modelo que se va a calcular. 0:Solar, 1:Eólica

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
			"ZonaHoraria": "str",
			"Altitud": "float",
			"Albedo": "float",
			"L": "float",
			"Cen": "float",
			"Ihf": "float",
			"InformacionMedida": "bool",
			"Kin": "float",
			"Kpc": "float",
			"Kt": "float",
			"Latitud": "float",
			"Longitud": "float",
			"NombrePlanta": "str",
			"Ppi": "float"
		},
		"ParametrosConfiguracion": {
			"GrupoInversores": [
				{
					"ParametrosInversor": {
						"NInv": "int",
						"PACnocturnoW": "float",
						"PACnominal": "float",
						"PDCarranque": "float",
						"PDCnominal": "float",
						"PowerAc": ["float"], //7 Valores
						"PowerDc": ["float"], //7 Valores
						"ReferenciaInversor": "str",
						"VDCnominal": "float"
					},
					"ParametrosModulo": {
						"AlphaSc": "float",
						"AltoFilaPaneles": "float",
						"AnchoFilaPaneles": "float",
						"BetaOc": "float",
						"Bifacial": "bool",
						"Bifacialidad": "float",
						"GammaPmp": "float",
						"Impstc": "float",
						"Iscstc": "float",
						"Ns": "int",
						"Pnominalstc": "float",
						"Psi": "float",
						"ReferenciaModulo": "str",
						"Tecnologia": {
							"Value": "str"
						},
						"Tnoct": "float",
						"Vmpstc": "float",
						"Vocstc": "float"
					},
					"EstructuraYConfiguracion": {
						"CantidadPanelConectados": [
							{
								"CantidadParalero": "int",
								"CantidadSerie": "int",
								"Id": "int",
								"OAzimutal": "float",
								"OElevacion": "float",
								"OMax": "float",
								"Racking": {
									"Value": "str"
								}
							}							
						],
						"EstructuraPlantaConSeguidores": "bool",
						"NSubarrays": "int"
					}
				}
			]
		},
		"ArchivoSeries": {
			"Nombre": "str",

		},
		"IdConexionWs": "str", //Siempre vacio.
		"IdTransaccion": "str", //Siempre vacio.
		"IdAplicacion": "str" //Siempre vacio.
	},
	"TipoMensaje": "int" //0:Solar.
}
```

**Ejemplo modelo Eólico**
- El archivo Parquet debe ser almacenado en el repositorio de Blob Storage o localmente. Si deseas ejecutar el código localmente, ajusta el código para que pueda leer un archivo Parquet desde una ruta "df = pl.read_parquet(self.archivo_blob)". Puedes encontrar la plantilla xlsx correspondiente en la aplicación web y este debera ser convertido a parquet.
```json
{
	"CuerpoMensaje": {
		"IdConexionWs": "",
		"ParametrosTransversales": {
			"NombrePlanta": "str",
			"Cen": "float",
			"Ihf": "float",
			"Ppi": "float",
			"InformacionMedida": "bool",
			"Offshore": "bool",
			"Kpc": "float",
			"Kt": "float",
			"Kin": "float",
			"Latitud": "float",
			"Longitud": "float",
			"Elevacion": "float",
			"Voltaje": "float"
		},
		"ParametrosConfiguracion": {
			"SistemasDeMedicion": [
				{
					"IdentificadorTorre": "str",
					"Latitud": "float",
					"Longitud": "float",
					"Elevacion": "float",
					"RadioRepresentatividad": "float",
					"CantidadAnemometro": "int",
					"ConfiguracionAnemometro": [
						{
							"Anemometro": "int",
							"AlturaAnemometro": "float"
						}
					],
					"ArchivoSeriesRelacionado": "str"
				}
			],
			"Aerogeneradores": [
				{
					"ModeloAerogenerador": "str",
					"AlturaBuje": "float",
					"DiametroRotor": "float",
					"PotenciaNominal": "float",
					"VelocidadNominal": "float",
					"DensidadNominal": "float",
					"VelocidadCorteInferior": "float",
					"VelocidadCorteSuperior": "float",
					"TemperaturaAmbienteMinima": "float",
					"TemperaturaAmbienteMaxima": "float",
					"CurvasDelFabricante": [
						{
							"SerieVelocidad": "float",
							"SeriePotencia": "float",
							"SerieCoeficiente": "float",
						}						
					],
					"CantidadAerogeneradores": "int",
					"EspecificacionesEspacialesAerogeneradores": [
						{
							"Aerogenerador": "int",
							"Latitud": "float",
							"Longitud": "float",
							"Elevacion": "float",
							"MedicionAsociada": {
								"Value": "str"
							}
						}
					]
				}
			],
			"ParametroConexion": [
				{
					"Conexion": "int",
					"CantidadAerogeneradoresConexion": "int",
					"Resistencia": "float",
					"ConexionAerogenerador": [
						{
							"OrdenConexion": "int",
							"IdentificadorAerogenerador": "int"
						},
					]
				}
			]
		},
		"ArchivoSeries": {
			"Nombre": "str"			
		}
	},
	"TipoMensaje": "int"  //1: Eólica
}
```
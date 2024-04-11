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

Solar
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
			"NombrePlanta": "Nombre planta solar",
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
						"ReferenciaInversor": "Huawei_Technologies_SUN2000_215KTL_H0",
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
			"Nombre": "02343839-24aa-4537-8412-765d891df9ef_SERIES.parquet"
		},
		"IdConexionWs": "",
		"IdTransaccion": "",
		"IdAplicacion": ""
	},
	"TipoMensaje": 0
}
```

Solar
```json
{

}
```
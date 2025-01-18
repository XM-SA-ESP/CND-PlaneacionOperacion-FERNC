import os
from XM_FERNC_API.dominio.servicio.azure_blob.cliente_azure import generar_archivo_excel_y_subir_volumen

class GenerarArchivoExcel:
    def __init__(self, manipulador_df, tipo_mensaje=None):
        self.manipulador_df = manipulador_df
        self.tipo_mensaje = tipo_mensaje

    def generar_archivo_excel(
        self, energia_planta, energia_mes, energia_diaria, enficc, eda, nombre_archivo
    ):        
        energia_planta = self.manipulador_df.transform_energia_planta(energia_planta)
        energia_mes = self.manipulador_df.transform_energia_mes(energia_mes)
        energia_diaria = self.manipulador_df.transform_energia_diaria(energia_diaria)
        df_enficc = self.manipulador_df.transform_enficc(enficc)
        df_eda = self.manipulador_df.transform_eda(eda)
        # Crear un diccionario donde cada clave es el nombre de una hoja,
        # y cada valor es un DataFrame o Serie que quieres escribir en esa hoja        

        diccionario_hojas = {
            "E_Horaria": energia_planta,
            "E_Mensual": energia_mes,
            "Em": energia_diaria,
            "ENFICC": df_enficc,
            "EDA": df_eda,
        }

        # Llamar a la función generar_archivo_excel_y_subir para escribir los DataFrames
        # en el archivo Excel y subirlo a Azure Blob Storage 
                        
        generar_archivo_excel_y_subir_volumen(
            diccionario_hojas, nombre_archivo
        )

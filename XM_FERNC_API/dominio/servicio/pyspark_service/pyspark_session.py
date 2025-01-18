import os
import sys
from pyspark.sql import SparkSession

def generar_sesion()-> SparkSession:
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

    spark = SparkSession.builder \
        .appName("StandaloneSpark") \
        .config("spark.master", "local") \
        .getOrCreate()
    return spark     
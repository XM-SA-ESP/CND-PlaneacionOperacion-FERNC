import warnings

from dotenv import load_dotenv
from shapely.errors import ShapelyDeprecationWarning
from urllib3.exceptions import InsecureRequestWarning

from utils.manejador_service_bus import ManejadorServiceBus

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

load_dotenv()

def main():
    service_bus_client = ManejadorServiceBus()
    service_bus_client.consumir_service_bus()

if __name__ == "__main__":
    print("Iniciando escucha de Service bus...")
    main() #Se queda escuchando en la cola del service bus por la vida util de la aplicación
import time
import os
from logging import ERROR, INFO, getLogger, StreamHandler, Formatter
from azure.monitor.opentelemetry import configure_azure_monitor

def timer(start,end):
   hours, rem = divmod(end-start, 3600)
   minutes, seconds = divmod(rem, 60)
   return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)

class DbLogger:

    def __init__(self, 
                 logg_type: str, 
                 logformat: str = '%(asctime)s [%(levelname)s] %(name)s: %(message)s') -> None:
        
        self.logg_type = logg_type
        self.logformat = logformat
        self.logger = None 

    def initialize_logger(self):
        if 'PYTEST_CURRENT_TEST' not in os.environ:
            configure_azure_monitor(logger_name=__name__)
            self.logger = getLogger(__name__)
            
            match self.logg_type:
                case "info":
                    self.logg_type = "info"
                    self.logger.setLevel(INFO)
                case "error":
                    self.logg_type = "error"
                    self.logger.setLevel(ERROR)
                case _:
                    raise ValueError("Tipo de mensaje no válido. Usa 'info' o 'error'.")
                
            self.stream_handler = StreamHandler()                
            self.formatter = Formatter(fmt=self.logformat)
            self.stream_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.stream_handler)

        else:
            print("Estamos en un entorno de test, no configuramos Azure Monitor")
    
    def send_logg(self, message: str, start=None) -> None:
        if self.logger != None:
            start = time.time() if start is None else start
            match self.logg_type:
                case "info":
                    self.logger.info(message + timer(start, time.time()))
                case "error":
                    self.logger.error(message + timer(start, time.time()))
        else:
            print(message)
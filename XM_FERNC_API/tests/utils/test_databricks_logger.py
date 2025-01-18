import unittest
from unittest.mock import patch, MagicMock
import time
import os

# Asumiendo que timer y DbLogger están en un módulo llamado 'mi_modulo'
from utils.databricks_logger import timer, DbLogger

class TestUtilities(unittest.TestCase):

    def test_timer(self):
        start_time = time.time()
        time.sleep(1)  # Simula un tiempo de espera
        end_time = time.time()

        formatted_time = timer(start_time, end_time)
        self.assertTrue(len(formatted_time) > 0)  # Verifica que se haya devuelto una cadena
        self.assertRegex(formatted_time, r'^\d{2}:\d{2}:\d{2}\.\d{2}$')  # Verifica el formato HH:MM:SS.sss


class TestDbLogger(unittest.TestCase):


    def setUp(self):
        self.mock_logger = MagicMock()
        self.mock_getLogger = self.mock_logger.return_value
        self.mock_getLogger.return_value = self.mock_logger


    @patch('utils.databricks_logger.os.environ')
    @patch('utils.databricks_logger.configure_azure_monitor')
    @patch('utils.databricks_logger.getLogger')
    def test_initialize_logger_info(self, mock_getLogger, mock_configure_azure_monitor, mock_os_environ):
        
        mock_os_environ.return_value = {}
        mock_obj = MagicMock()
        mock_obj.setLevel.retrun_value = None 
        mock_getLogger.return_value = mock_obj
        
        mock_configure_azure_monitor.retrun_value = None
        
        db_logger = DbLogger("info")
        db_logger.initialize_logger()
        mock_obj.setLevel.assert_called_once()

    @patch('utils.databricks_logger.os.environ')
    @patch('utils.databricks_logger.configure_azure_monitor')
    @patch('utils.databricks_logger.getLogger')
    def test_initialize_logger_error(self, mock_getLogger, mock_configure_azure_monitor, mock_os_environ):
        
        mock_os_environ.return_value = {}
        mock_obj = MagicMock()
        mock_obj.setLevel.retrun_value = None 
        mock_getLogger.return_value = mock_obj
        
        mock_configure_azure_monitor.retrun_value = None
        
        db_logger = DbLogger("error")
        db_logger.initialize_logger()
        mock_obj.setLevel.assert_called_once()

    @patch('utils.databricks_logger.os.environ')
    @patch('utils.databricks_logger.configure_azure_monitor')
    @patch('utils.databricks_logger.getLogger')
    def test_initialize_logger_error_case(self, mock_getLogger, mock_configure_azure_monitor, mock_os_environ):
        
        mock_os_environ.return_value = {}
        mock_obj = MagicMock()
        mock_obj.setLevel.retrun_value = None 
        mock_getLogger.return_value = mock_obj    
        mock_configure_azure_monitor.retrun_value = None
        
        with self.assertRaises(ValueError) as context:
            db_logger = DbLogger("test")
            db_logger.initialize_logger()

        # Verificar el mensaje del ValueError
        self.assertEqual(str(context.exception), "Tipo de mensaje no válido. Usa 'info' o 'error'.")

    @patch('builtins.print')
    @patch('utils.databricks_logger.configure_azure_monitor')
    @patch('utils.databricks_logger.getLogger')
    def test_initialize_logger_entorno_test(self, mock_getLogger, mock_configure_azure_monitor, mock_print):
        
        db_logger = DbLogger("test")
        db_logger.initialize_logger()
        mock_print.assert_called_with("Estamos en un entorno de test, no configuramos Azure Monitor")

        
    @patch('utils.databricks_logger.os.environ')
    @patch('utils.databricks_logger.configure_azure_monitor')
    @patch('utils.databricks_logger.getLogger')
    @patch('time.time', return_value=0)  # Mockeamos time.time
    def test_send_logg_info(self, mock_time, mock_getLogger, mock_configure_azure_monitor, mock_os_enviroment):
        db_logger = DbLogger("info")
        db_logger.initialize_logger()

        db_logger.send_logg("Test message")
        #self.mock_logger.info.assert_called_once_with("Test message 00:00:00.00")

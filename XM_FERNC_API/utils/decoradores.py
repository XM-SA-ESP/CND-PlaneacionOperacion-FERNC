import functools

from XM_FERNC_API.utils.manipulador_excepciones import BaseExcepcion
from XM_FERNC_API.utils.databricks_logger import DbLogger


def capturar_excepciones(tarea: str, mensaje: str, exep: BaseExcepcion):
    logger = DbLogger('error')
    def decorador(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:

                return func(*args, **kwargs)
            except Exception as error:

                if isinstance(error, BaseExcepcion):
                    logger.initialize_logger()
                    logger.send_logg(error)
                    raise error

                print(
                    f"Se ha producido una excepción en la función {func.__name__}: {error}"
                )
                logger.initialize_logger()
                logger.send_logg(f"Se ha producido una excepción en la función {func.__name__}: {error} | {mensaje}")
                raise exep(error, tarea, mensaje)
        return wrapper
    return decorador

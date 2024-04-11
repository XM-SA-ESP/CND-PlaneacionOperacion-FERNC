import functools

from utils.manipulador_excepciones import BaseExcepcion

def capturar_excepciones(tarea: str, mensaje: str, exep: BaseExcepcion):
    def decorador(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:

                return func(*args, **kwargs)
            except Exception as error:

                if isinstance(error, BaseExcepcion):
                    raise error

                print(
                    f"Se ha producido una excepción en la función {func.__name__}: {error}"
                )
                raise exep(error, tarea, mensaje)
        return wrapper
    return decorador

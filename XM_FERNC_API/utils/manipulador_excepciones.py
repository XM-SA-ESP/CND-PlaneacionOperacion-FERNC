class ManipuladorExcepciones:
    def __init__(self, error, mensaje_tarea, mensaje_error) -> None:
        self.error = error
        self.mensaje_tarea = mensaje_tarea
        self.mensaje_error = mensaje_error

    def obtener_error(self):
        return str(self.error)

    def obtener_mensaje_tarea(self):
        return self.mensaje_tarea

    def obtener_mensaje_error(self):
        return self.mensaje_error

class BaseExcepcion(Exception):
    """Excepción personalizada para errores en cálculos."""

    def __init__(self, error: str, tarea: str = "", mensaje: str = ""):
        """
        Inicializa la excepción.

        Args:
            error (str): Descripción del error.
            tarea (str): Tarea o contexto en el que ocurrió el error.
            mensaje (str): Mensaje adicional para proporcionar detalles sobre el error.
        """
        super().__init__(f"Error en '{tarea}': {error}. {mensaje}")
        self._error = error
        self._tarea = tarea 
        self._mensaje = mensaje 

    @property
    def error(self) -> str:
        """Obtiene la descripción del error."""
        return self._error

    @property
    def tarea(self) -> str:
        """Obtiene la tarea o contexto en el que ocurrió el error."""
        return self._tarea

    @property
    def mensaje(self) -> str:
        """Obtiene el mensaje adicional para proporcionar detalles sobre el error."""
        return self._mensaje

class CalculoExcepcion(BaseExcepcion):
    """Excepción personalizada para errores en cálculos."""

    def __init__(self, error: str, tarea: str, mensaje: str):
        """
        Inicializa la excepción para errores en cálculos.

        Args:
            error (str): Descripción del error.
            tarea (str): Tarea o contexto en el que ocurrió el error.
            mensaje (str): Mensaje adicional para proporcionar detalles sobre el error.
        """
        super().__init__(error, tarea, mensaje)

class CurvasExcepcion(BaseExcepcion):
    """Excepción personalizada para errores relacionados con curvas."""

    def __init__(self, error: str, tarea: str, mensaje: str):
        """
        Inicializa la excepción para errores relacionados con curvas.

        Args:
            error (str): Descripción del error.
            tarea (str): Tarea o contexto en el que ocurrió el error.
            mensaje (str): Mensaje adicional para proporcionar detalles sobre el error.
        """
        super().__init__(error, tarea, mensaje)

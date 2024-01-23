from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from infraestructura.api.eolica.routes import router_eolica
from infraestructura.api.solar.routes import router_solar

import warnings
from shapely.errors import ShapelyDeprecationWarning

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print('Error:', exc.errors())
    return JSONResponse(
        status_code=422,  # Código de estado personalizado
        content={"details": exc.errors()},  # Detalles completos de la validación
    )

app.include_router(router_eolica)
app.include_router(router_solar)

load_dotenv()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8800, reload=True)

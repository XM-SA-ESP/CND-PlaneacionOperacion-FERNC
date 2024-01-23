FROM python:3.11.1-slim

WORKDIR /app
COPY . /app


# Instala las dependencias si tienes un archivo requirements.txt
RUN pip install -r requirements.txt

EXPOSE 443
EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
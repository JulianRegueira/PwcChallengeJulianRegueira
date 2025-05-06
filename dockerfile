# Dockerfile
FROM python:3.10-slim

# Crea carpeta de la app
WORKDIR /app

# Copia archivos de requisitos
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto de la API
EXPOSE 8000

# Punto de entrada
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
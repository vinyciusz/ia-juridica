# 🔹 Escolhe a versão do Python que será usada no ambiente
FROM python:3.9

# 🔹 Atualiza os pacotes do sistema operacional e instala o Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils

# 🔹 Define um diretório de trabalho dentro do container
WORKDIR /app

# 🔹 Copia todos os arquivos do projeto para dentro do container
COPY . .

# 🔹 Instala todas as bibliotecas do Python necessárias
RUN pip install --no-cache-dir -r requirements.txt

# 🔹 Expõe a porta 8080, que é a usada pelo Railway
EXPOSE 8080

# 🔹 Comando final que inicia a API FastAPI no servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

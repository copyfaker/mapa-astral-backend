# Usa imagem oficial do Python 3.11
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Copia tudo para o container
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta (se usar web)
EXPOSE 8000

# Comando para iniciar
CMD ["python", "app.py"]

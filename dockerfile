    # Usamos uma imagem oficial do Python como base
    FROM python:3.9-slim
    
    # Define o diretório de trabalho dentro do container
    WORKDIR /app
    
    # Copia o arquivo de dependências para o diretório de trabalho
    COPY requirements.txt .
    
    # Instala as dependências listadas no requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Copia todo o código da aplicação para o diretório de trabalho
    COPY . .
    
    # Expõe a porta 5000, que é a porta que o Flask vai usar
    EXPOSE 5000
    
    # Comando para iniciar a aplicação quando o container for executado
    CMD ["python", "app/main.py"]
    
# Use a imagem oficial do Python com a versão desejada
FROM python:3.12.4

# Instala as dependências do sistema necessárias, incluindo o driver ODBC
RUN apt-get update \
    && apt-get install -y unixodbc-dev \
    && apt-get install -y g++ \
    && apt-get install -y curl

# Adiciona o repositório do Microsoft ODBC Driver 17 para SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Instala o driver ODBC
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos necessários para o diretório de trabalho
COPY requirements.txt /app/

# Instala as dependências da aplicação
RUN pip install --no-cache-dir -r requirements.txt

# Instala as dependências da aplicação
RUN pip install boto3

# Copia o restante dos arquivos da aplicação para o diretório de trabalho
COPY . /app/

# Exponha a porta na qual a aplicação Django estará escutando
EXPOSE 8000

# Comando para iniciar a aplicação Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

#python manage.py runserver  0.0.0.0:8000

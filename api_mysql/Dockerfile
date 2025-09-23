FROM python:3.10

RUN apt-get update -y && \
    apt-get install -y python3-pip

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip

RUN pip install boto3

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD $INTERPRETER $COMMAND
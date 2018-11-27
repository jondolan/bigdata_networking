FROM python:3

MAINTAINER Jon Dolan jondolan@gatech.edu

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "run.py"]

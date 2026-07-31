FROM python:3.8

WORKDIR /code

COPY Requirements.txt .

RUN pip install -r Requirements.txt

COPY . .

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg


CMD ["python", "ffmpeg"]
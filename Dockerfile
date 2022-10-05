FROM ubuntu:22.04

COPY ./src /app

RUN apt update

RUN apt install -y python3-pip iproute2

WORKDIR /app

RUN pip3 install -r requirements.txt

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
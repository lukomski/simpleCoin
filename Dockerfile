FROM python:3.11.0rc2-slim-buster

WORKDIR /app

COPY ./src/requirements.txt ./

RUN pip3 install -r requirements.txt

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
FROM python:3.11.0rc2-slim-buster

ENV FLASK_APP=app.py
ENV FLASK_RUN_PORT=5000
ENV FLASK_DEBUG=1

WORKDIR /app

COPY ./src/requirements.txt ./

RUN pip3 install -r requirements.txt

COPY ./src/ ./

RUN rm -r ./__pycache__

EXPOSE 5000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5000", "--with-threads", "--no-reload"]
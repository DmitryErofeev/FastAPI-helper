from python:3.9-alpine

WORKDIR /app

RUN python -m venv venv
COPY requirements.txt requirements.txt
RUN venv/bin/pip install -r requirements.txt

COPY . .
VOLUME /misc-volume

EXPOSE 8000
ENTRYPOINT ["venv/bin/python", "-m", "uvicorn", "--host","0.0.0.0","main:app"]

# Pull base image
FROM python:3.7.4

COPY app /usr/src/app
COPY tests /usr/src/tests
COPY .env /usr/src/
COPY requirements.txt /usr/src/

ENV PYTHONPATH /usr/src/

# Install dependencies
RUN pip install -r /usr/src/requirements.txt
CMD uvicorn app.main:app --host 0.0.0.0  --port 8080  --loop uvloop --workers 4
# Pull base image
FROM python:3.7.4

COPY app /usr/src/app
COPY tests /usr/src/tests
COPY .env /usr/src/
COPY requirements.txt /usr/src/

ENV PYTHONPATH /usr/src/

# Install dependencies
RUN pip install -r /usr/src/requirements.txt
CMD gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080
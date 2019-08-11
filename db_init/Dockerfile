FROM postgres:10.1-alpine

RUN rm -r -f /docker-entrypoint-initdb.d/
ADD init.sql /docker-entrypoint-initdb.d/

ENV POSTGRES_HOST 0.0.0.0
ENV POSTGRES_USER daler
ENV POSTGRES_PASSWORD daler
ENV POSTGRES_DB citizens_db
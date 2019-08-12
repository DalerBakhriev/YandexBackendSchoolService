FROM postgres:10.1-alpine

RUN rm -r -f /docker-entrypoint-initdb.d/
ADD init.sql /docker-entrypoint-initdb.d/
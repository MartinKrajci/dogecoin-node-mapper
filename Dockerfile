FROM python:3.10-alpine

COPY ./app /

RUN apk add gcc
RUN apk add g++
RUN apk add musl-dev
RUN apk add postgresql
RUN pip install sqlalchemy
RUN pip install psycopg2-binary

CMD PGPASSWORD=dogepass psql -U postgres -h db -c 'CREATE DATABASE dogecoin_mapper' || true; python create_db.py; python crawl.py; python ping_nodes.py

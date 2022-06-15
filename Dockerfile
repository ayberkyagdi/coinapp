FROM python:3.8.5-alpine

COPY /app /app

WORKDIR /app

RUN apk add gcc musl-dev mariadb-connector-c-dev build-base

RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python"]

CMD ["blog.py"]
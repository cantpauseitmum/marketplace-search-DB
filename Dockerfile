FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN python3 init_db.py --seed

CMD ["python3", "init_db.py", "--stats"]

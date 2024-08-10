FROM python:3.12

WORKDIR /

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.txt

COPY autohedge ./autohedge
COPY tests ./tests
COPY example.py ./

CMD ["python", "-m", "autohedge", "--version"]

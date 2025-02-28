# FROM agnohq/python:3.12
FROM python:3.9

WORKDIR /app

# Install system dependencies including swig
# RUN apt-get update && apt-get install -y \
#     swig \
#     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "playground.py", "--host", "0.0.0.0", "--port", "8000"]
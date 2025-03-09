FROM agnohq/python:3.12

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "upload_files.py", "--host", "0.0.0.0", "--port", "8000"] 
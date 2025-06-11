FROM python:3.11-alpine
ENV PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "main:app"]

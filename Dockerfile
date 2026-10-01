FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home keeper && mkdir /data && chown keeper:keeper /data
COPY . .
USER keeper
EXPOSE 8765
CMD ["python", "server.py"]

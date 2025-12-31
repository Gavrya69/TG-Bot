FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY core.py core.py
COPY main.py main.py
COPY req.txt req.txt
COPY .env .env
RUN pip install --no-cache-dir -r req.txt
RUN mkdir ./temp
CMD ["python", "main.py"]
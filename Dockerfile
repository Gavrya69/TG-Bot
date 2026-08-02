FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive
# yt-dlp requires Node.js >= 22 for YouTube JS challenges (Debian nodejs is too old).
ENV NODE_VERSION=22.17.1
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl xz-utils ffmpeg \
    && curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
       | tar -xJ -C /usr/local --strip-components=1 \
    && node --version \
    && npm --version \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir ./temp
CMD ["python", "video downloader_bot/main.py"]

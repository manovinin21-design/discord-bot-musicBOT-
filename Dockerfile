# Imagem do bot para o Render (o ambiente Python nativo deles não tem
# ffmpeg nem libopus, que o player de música precisa)
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libopus0 \
    && rm -rf /var/lib/apt/lists/*

# Runtime JavaScript que o yt-dlp usa para resolver os desafios do
# YouTube — sem ele as músicas ficam lentas ou nem tocam
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

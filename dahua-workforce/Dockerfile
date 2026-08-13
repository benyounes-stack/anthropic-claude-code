# Image du collecteur et du générateur de rapport.
#
# Chromium (pour le rendu PDF) et onnxruntime (pour la détection) sont tous deux
# embarqués : la même image sert au service continu et à la tâche quotidienne.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers

# Node est requis par le script de rendu de la skill custom-reports.
RUN apt-get update && apt-get install -y --no-install-recommends \
        nodejs npm ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g playwright@1.56.1 \
    && npx --yes playwright@1.56.1 install --with-deps chromium

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps -e .

# La skill custom-reports (gabarit HTML, charte, script de rendu) est montée
# depuis le dépôt au lancement — voir docker-compose.yml.

ENTRYPOINT ["workforce"]
CMD ["--help"]

FROM python:3.12-slim-bookworm

ARG DEBIAN_MIRROR=mirrors.ustc.edu.cn
ARG PYPI_INDEX_URL=https://mirrors.ustc.edu.cn/pypi/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN sed -i "s|deb.debian.org|${DEBIAN_MIRROR}|g" \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install --no-install-recommends -y libcairo2 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app

COPY requirements.txt ./
RUN pip install --no-cache-dir \
        --index-url "${PYPI_INDEX_URL}" \
        -r requirements.txt

COPY --chown=app:app api_server.py url_to_svg.py logo.svg ./

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["python", "api_server.py", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir Flask==3.1.3 \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin lab \
    && setcap -r /usr/bin/ping \
    && ln -s /tmp/flag.txt /flag.txt
WORKDIR /app
COPY --chown=10001:10001 labs/week04-injection/vulnerable_app.py /app/vulnerable_app.py

USER 10001:10001
EXPOSE 5000
# seed() writes through /flag.txt -> /tmp/flag.txt, so the intended command-
# injection flag remains testable while the root filesystem stays read-only.
CMD ["python", "-c", "import vulnerable_app as v; v.seed(); v.app.run(host='0.0.0.0', port=5000, debug=False)"]

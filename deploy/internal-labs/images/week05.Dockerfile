FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --no-cache-dir Flask==3.1.3 \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin lab
WORKDIR /app
COPY --chown=10001:10001 labs/week05-xss-client-side/vulnerable_app.py /app/vulnerable_app.py

USER 10001:10001
EXPOSE 5000
CMD ["python", "-c", "import vulnerable_app as v; v.app.run(host='0.0.0.0', port=5000, debug=False)"]

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY project/starter-app/requirements.txt /tmp/requirements.txt
# These old pins are intentional project findings. They are isolated here; do
# not reuse this image as a base for the learning/control application.
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin lab
COPY --chown=10001:10001 project/starter-app/app.py /app/app.py
COPY --chown=10001:10001 project/starter-app/templates /app/templates
COPY --chown=10001:10001 project/starter-app/static /app/static

USER 10001:10001
EXPOSE 8080
CMD ["python", "-c", "import app; app.seed(); app.app.run(host='0.0.0.0', port=8080, debug=False)"]

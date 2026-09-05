FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY labs/week01-threat-modeling/sample-app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin lab
COPY --chown=10001:10001 labs/week01-threat-modeling/sample-app/app.py /app/app.py

USER 10001:10001
EXPOSE 5000
# The unmodified lesson uses relative SQLite/upload paths. Running from the
# tmpfs keeps the image immutable without changing what students exercise.
CMD ["python", "-c", "import os,sys; os.chdir('/tmp'); sys.path.insert(0,'/app'); import app; app.init_db(); app.app.run(host='0.0.0.0', port=5000, debug=False)"]

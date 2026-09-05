FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
# Keep the planted alg:none branch in vulnerable_app.py, but do not add
# unrelated library-level JWT bypasses to the exercise image.
RUN pip install --no-cache-dir Flask==3.1.3 PyJWT==2.13.0 \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin lab
WORKDIR /app
COPY --chown=10001:10001 labs/week06-authn-authz/vulnerable_app.py /app/vulnerable_app.py

USER 10001:10001
EXPOSE 5000
CMD ["python", "-c", "import vulnerable_app as v; v.app.run(host='0.0.0.0', port=5000, debug=False)"]

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
ARG LAB_DIR
WORKDIR /lab
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir flask==3.1.3 \
    && groupadd --gid 10001 lab \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin lab
COPY ${LAB_DIR}/ /lab/
USER 10001:10001
EXPOSE 5000
# The operator chooses the known lesson module; a request cannot choose code.
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000", "--no-debugger", "--no-reload"]

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CONTENT_ROOT=/content/labs

WORKDIR /app
COPY labs/live-quiz/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt
COPY labs/live-quiz/ /app/
COPY labs/ /content/labs/
COPY slides/ /content/slides/
COPY SUBMISSION.md ETHICS.md /content/
COPY quizzes/ /content/quizzes/
COPY project/ /content/project/

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && install -d -o 10001 -g 10001 -m 0700 /data \
    && chown -R 10001:10001 /app /content

USER 10001:10001
EXPOSE 5000
CMD ["python", "app.py"]

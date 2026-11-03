ARG PYTHON_BASE=python:3.12-slim
FROM ${PYTHON_BASE}
RUN pip install --no-cache-dir math-verify==0.9.0 evalplus==0.3.1
COPY src/coreta/scoring_worker.py /opt/coreta-scoring-worker.py
ENV PYTHONDONTWRITEBYTECODE=1
USER 65532:65532
WORKDIR /tmp

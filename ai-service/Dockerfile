FROM python:3.12-slim
WORKDIR /srv/ai-service
COPY ai-service/pyproject.toml ./
RUN pip install --no-cache-dir .
COPY ai-service/app ./app
COPY dataset /srv/dataset
RUN useradd --uid 10001 --create-home reqguard
USER reqguard
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

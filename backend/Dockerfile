FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh \
    && addgroup --system finpilot \
    && adduser --system --ingroup finpilot finpilot \
    && chown -R finpilot:finpilot /app
USER finpilot
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]

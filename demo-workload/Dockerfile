FROM --platform=linux/amd64 python:3.12-slim

# forces Python to send output straight to the terminal 
# forces Python to skip saving byte code cached files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

# dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./app/

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"]

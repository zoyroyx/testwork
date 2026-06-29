FROM python:3.11-slim as builder

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim as runner

WORKDIR /code

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Convert line endings of entrypoint script to LF to prevent issues on Windows hosts
RUN sed -i 's/\r$//' scripts/entrypoint.sh && chmod +x scripts/entrypoint.sh

ENTRYPOINT ["scripts/entrypoint.sh"]

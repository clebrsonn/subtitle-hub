FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Set up non-root user
RUN adduser --disabled-password --gecos '' myuser && \
    mkdir -p /app/managed_media && \
    chown -R myuser:myuser /app

USER myuser

# Expose port
EXPOSE 8000

# Run gunicorn bound to 0.0.0.0 inside the container so compose port mapping works
CMD ["gunicorn", "subtitle_hub.wsgi:application", "--bind", "0.0.0.0:8000"]

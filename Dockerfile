FROM python:3.11-slim

# Environment and working directory
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PORT=8501 \
	STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install dependencies first for better build caching
COPY requirements.txt /app/
RUN pip install --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application (respects .dockerignore)
COPY . /app

# Expose the port used by Streamlit
EXPOSE ${PORT}

# Run the Streamlit app on the configured $PORT and bind to all interfaces
CMD ["bash", "-lc", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true"]
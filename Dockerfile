# Use Python 3.11 slim image for compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .
COPY rizzk_core.py .
COPY test_risk_reward.py .

# Set default port and expose it so platform routers can reach the container
ENV PORT=8501
EXPOSE ${PORT}

# Run the Streamlit app on the configured $PORT and bind to all interfaces
CMD ["bash", "-lc", "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"]
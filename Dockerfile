# Use the official Python image with the latest version
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 8000

# Start the server using Uvicorn
CMD ["uvicorn", "task_manager:app", "--host", "0.0.0.0", "--port", "8000"]

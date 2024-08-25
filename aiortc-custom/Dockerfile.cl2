# Use the official Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port your service runs on
EXPOSE 8080

# Define the command to run your service
ENTRYPOINT ["python", "aiortc_2.py"]
CMD ["--port","8081","--cert-file","server.crt","--key-file","server.key"]
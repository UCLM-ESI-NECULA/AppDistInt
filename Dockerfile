FROM python:3.9-slim

WORKDIR /usr/src/app

COPY . .

# Install the remaining packages in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and switch to it
RUN useradd -m user
USER user

# Make port 3002 available to the world outside this container
EXPOSE 3002

# Define environment variable
ENV BLOB_SERVICE_PORT=3002

# Run the application when the container launches
CMD ["python", "blobapi/server.py"]

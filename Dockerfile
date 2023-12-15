FROM python:slim

WORKDIR /usr/src/app

COPY . .

# Install the remaining packages in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and switch to it
RUN useradd -m user

# Set permissions for the non-root user
RUN chown -R user:user /usr/src/app

USER user

# Expose port 3002
EXPOSE 3002

# Define default environment variable
ENV BLOB_SERVICE_PORT=3002

# Run the application when the container launches
CMD ["python", "-m",  "blobapi.server"]

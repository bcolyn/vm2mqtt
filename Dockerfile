# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -g 1001 vm2mqtt && \
    useradd -m -u 1001 -g vm2mqtt vm2mqtt

USER vm2mqtt:vm2mqtt

# Copy the current directory contents into the container at /app
COPY src .

# Run app.py when the container launches
CMD ["python", "main.py"]

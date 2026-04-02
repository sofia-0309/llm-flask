# python 3.9 as base image
FROM python:3.9-slim

# set working directory
WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy application code
COPY . .

EXPOSE 5001

# start flask application
CMD ["python", "app.py"]

ENV PYTHONUNBUFFERED=1
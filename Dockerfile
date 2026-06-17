# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /code

# Copy requirements first to leverage Docker caching
COPY ./requirements.txt /code/requirements.txt

# Install all Python dependencies inside the container
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the application code
COPY ./app /code/app

# Copy the .env file so the app can read it via os.getenv()
COPY ./.env /code/.env

# Command to run uvicorn when the container starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# CMD ["sh", "-c", "npm run dev & uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
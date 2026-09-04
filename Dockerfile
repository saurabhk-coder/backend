FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . /src
 
WORKDIR /src
RUN pip install --upgrade pip
RUN apt-get update
RUN pip install -r requirements.txt
EXPOSE 86

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]


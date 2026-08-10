FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY . /src
 
WORKDIR /src
RUN pip install --upgrade pip
RUN apt-get update
RUN pip install -r requirements.txt
EXPOSE 86

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]


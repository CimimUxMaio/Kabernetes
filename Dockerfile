FROM python:3.8.10
WORKDIR /kabernetes
COPY . .
RUN pip install -r ./requirements.txt
ENTRYPOINT ["python", "main.py" ]
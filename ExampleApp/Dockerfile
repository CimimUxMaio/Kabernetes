FROM python:3.8.10
WORKDIR /app
COPY . .
RUN pip install flask
ENV VIRTUAL_HOST kabernetes.example-app.com
ENTRYPOINT [ "python", "main.py" ]
FROM python:3.8.10
WORKDIR /app
COPY . .
RUN pip install flask
EXPOSE 5000
ENV VIRTUAL_HOST kabernetes.example-app.com
ENTRYPOINT [ "python", "main.py" ]
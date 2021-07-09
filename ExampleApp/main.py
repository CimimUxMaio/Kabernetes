import threading

from flask import Flask

COMPLEXITY = 3000000

app = Flask(__name__)


class Worker(threading.Thread):
    def __init__(self):
        super(Worker, self).__init__(daemon=True)

    def run(self):
        for _ in range(COMPLEXITY):
            pass


@app.route("/resource")
def resource():
    worker = Worker()
    worker.start()
    return f"Resource obtained."


if __name__ == '__main__':
    app.run(host="0.0.0.0")

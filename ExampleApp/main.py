from flask import Flask
import os

COMPLEXITY = 100000000


app = Flask(__name__)

@app.route("/resource")
def resource():
    for _ in range(COMPLEXITY):
        pass

    return f"Resource obtained from proces {os.getpid()}"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
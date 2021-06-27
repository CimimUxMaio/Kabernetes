from flask import Flask

COMPLEXITY = 100000000


app = Flask(__name__)

@app.route("/resource")
def resource():
    for _ in range(COMPLEXITY):
        pass

    return "Resource obtained"


if __name__ == '__main__':
    app.run()
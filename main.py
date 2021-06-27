from flask.json import jsonify
from config import CONFIG
from src.kabernetes import Kabernetes
from flask import Flask, request
from errors import AppError
from errors import NoClientRunning, ClientAlreadyRunning, BadConfig


app = Flask(__name__)
client = None 

def client_running():
    global client
    return client and client.is_alive()


def check_config(config):
    if not all(key in ["image", "cpu_target", "constants"] for key in config.keys()):
        raise BadConfig()


@app.errorhandler(AppError)
def handle_app_error(e):
    return e.message, e.code


@app.route("/client")
def stats():
    if not client_running():
        raise NoClientRunning()

    global client
    return jsonify(client.stats())


@app.route("/client", methods=["POST"])
def start_client():
    config = request.json if request.json else {}
    check_config(config)
    if client_running():
        raise ClientAlreadyRunning()

    global client
    client = Kabernetes(config["image"], config["cpu_target"], config["constants"])
    client.start()
    return "Client started"


@app.route("/client", methods=["PUT"])
def update_constants():
    if not client_running():
        raise NoClientRunning()

    constants = request.json if request.json else {}
    global client
    client.set_constants(constants)
    return "Constants updated"


@app.route("/client", methods=["DELETE"])
def stop_client():
    if not client_running():
       raise NoClientRunning()

    global client
    client.end()
    client.join()
    return "Client deleted"


if __name__ == '__main__':
    app.run(host=CONFIG["host"], port=CONFIG["port"])
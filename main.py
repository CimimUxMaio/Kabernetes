from flask.json import jsonify
from config import CONFIG
from src.kabernetes import Kabernetes
from flask import Flask, request
from errors import AppError, NegativeContainerNumber, WrongBodyFormat
from errors import NoClientRunning, ClientAlreadyRunning


app = Flask(__name__)
client: Kabernetes = None 


def client_running():
    global client
    return client and client.is_alive()

def check_condition(value, exception_constructor):
    if value:
        raise exception_constructor()

def check_dict_for_keys(dict_, keys):
    check_condition(
        value=not bool(dict_) or not all(key in dict_.keys() for key in keys), 
        exception_constructor = lambda: WrongBodyFormat(keys)
    )

def check_config(config):
    check_dict_for_keys(config, ["image", "cpu_target", "constants"])


def check_container_amount(amount):
    if amount < 0:
        raise NegativeContainerNumber(amount)

def check_client_running():
    check_condition(
        value=client_running(),
        exception_constructor=lambda: ClientAlreadyRunning()
    )

def check_client_not_running():
    check_condition(
        value=not client_running(),
        exception_constructor=lambda: NoClientRunning()
    )


@app.errorhandler(AppError)
def handle_app_error(e):
    return e.message, e.code


@app.route("/client")
def stats():
    check_client_not_running()

    global client
    return jsonify(client.stats())


@app.route("/client", methods=["POST"])
def start_client():
    check_client_running()
    config = request.json
    check_config(config)

    global client
    client = Kabernetes(config["image"], config["cpu_target"], { k: float(v) for k, v in config["constants"]})
    client.start()
    return "Client started"


@app.route("/client", methods=["PATCH"])
def update_constants():
    check_client_not_running()

    constants = { k: float(v) for k, v in request.json } if request.json else {}
    global client

    client.set_constants(constants)
    return "Constants updated"


@app.route("/client", methods=["DELETE"])
def stop_client():
    check_client_not_running()

    global client
    client.end()
    client.join()
    return "Client deleted"


@app.route("/client/containers", methods=["DELETE"])
def drop_containers():
    check_client_not_running()
    body = request.json
    check_dict_for_keys(body, ["amount"])
    amount = body["amount"]
    check_container_amount(amount)

    global client
    client.kill_containers(amount)
    return "Container dropped"
    

@app.route("/client/containers", methods=["POST"])
def push_container():
    check_client_not_running() 
    body = request.json
    check_dict_for_keys(body, ["amount"])
    amount = body["amount"]
    check_container_amount(amount)

    global client
    client.create_containers(amount)
    return "Container pushed"


if __name__ == '__main__':
    app.run(host=CONFIG["host"], port=CONFIG["port"])
from flask import Flask, request
from flask.json import jsonify

from config import CONFIG
from errors import AppError, ClientNotAvailable, ClientNotInitialized, NegativeContainerNumber, NotEnoughContainers, \
    NumericValue, WrongBodyFormat
from errors import ClientNotInstantiated, ClientAlreadyRunning
from src.kabernetes import Kabernetes

app = Flask(__name__)
client: Kabernetes = None


def check_dict_for_keys(dict_, keys):
    if not bool(dict_) or not all(key in dict_.keys() for key in keys):
        raise WrongBodyFormat(keys)


def check_config(config):
    check_dict_for_keys(config, ["image", "cpu_target", "constants"])


def check_container_amount(amount):
    if amount < 0:
        raise NegativeContainerNumber(amount)


def check_client_initialized():
    global client
    if not client.is_initialized():
        raise ClientNotInitialized()


def client_instantiated():
    global client
    return bool(client)


def check_client_instantiated():
    if not client_instantiated():
        raise ClientNotInstantiated()


def check_client_instantiated_and_available():
    check_client_instantiated()

    global client
    if not client.is_available():
        raise ClientNotAvailable()


def check_client_not_running():
    global client
    if client and not client.is_dead():
        raise ClientAlreadyRunning()


def clean_numeric(name, value):
    try:
        return float(value)
    except ValueError:
        raise NumericValue(name)


def clean_constants(constants):
    final = {}
    for k, v in constants.items():
        final[k] = clean_numeric(k, v) if v else 0

    return final


@app.errorhandler(AppError)
def handle_app_error(e):
    return e.message, e.code


@app.route("/client")
def stats():
    check_client_instantiated()
    check_client_initialized()

    global client
    return jsonify(client.stats())


@app.route("/client", methods=["POST"])
def start_client():
    check_client_not_running()
    config = request.json
    check_config(config)

    global client
    client = Kabernetes(config["image"], clean_numeric("cpu_target", config["cpu_target"]),
                        clean_constants(config["constants"]))
    client.start()
    return "Client started"


@app.route("/client", methods=["PATCH"])
def update_constants():
    check_client_instantiated_and_available()
    constants = clean_constants(request.json) if request.json else {}
    global client

    client.set_constants(constants)
    return "Constants updated"


@app.route("/client", methods=["DELETE"])
def stop_client():
    check_client_instantiated_and_available()

    global client
    client.signal_end()
    client.join()
    return "Client deleted"


@app.route("/client/containers", methods=["DELETE"])
def drop_containers():
    check_client_instantiated_and_available()
    body = request.json
    check_dict_for_keys(body, ["amount"])
    amount = int(clean_numeric("amount", body["amount"]))
    check_container_amount(amount)

    global client
    if (client.container_amount - amount) <= 0:  # client.container_amount - 1 < amount:
        raise NotEnoughContainers()

    client.kill_containers(amount)
    return "Container dropped"


@app.route("/client/containers", methods=["POST"])
def push_container():
    check_client_instantiated_and_available()
    body = request.json
    check_dict_for_keys(body, ["amount"])
    amount = int(clean_numeric("amount", body["amount"]))
    check_container_amount(amount)

    global client
    client.create_containers(amount)
    return "Container pushed"


if __name__ == '__main__':
    app.run(host=CONFIG["host"], port=CONFIG["port"])

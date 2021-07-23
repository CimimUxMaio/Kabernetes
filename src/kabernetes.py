import enum
import math
import threading as th

import docker


class Status(enum.Enum):
    STARTING = 'STARTING'
    STOPPING = 'STOPPING'
    READY = 'READY'
    BUSY = 'BUSY'
    DEAD = 'DEAD'


class Kabernetes(th.Thread):
    def __init__(self, image, cpu_target, constants):
        super().__init__(daemon=True)
        self.image = image
        self.cpu_target = cpu_target

        self.docker_client = docker.from_env()

        self._constants = constants
        self._error_acum = 0
        self._end = False
        self._available = False
        self._status = Status.STARTING

        self._calculated_feedback = 0
        self._calculated_cpu_usage = []
        self._calculated_error = self._calculated_feedback - self.cpu_target
        self._last_error = self._calculated_error

    @property
    def kp(self):
        return self._constants.get("kp", 0)

    @property
    def kd(self):
        return self._constants.get("kd", 0)

    @property
    def ki(self):
        return self._constants.get("ki", 0)

    @property
    def container_list(self):
        return self.docker_client.containers.list()

    @property
    def status(self):
        return self._status

    @property
    def container_amount(self):
        return len(self.container_list)

    def container_stats(self):
        return [container.stats(stream=False) for container in self.container_list]

    def cpu_usage(self):
        self._calculated_cpu_usage = [self.calculate_cpu_usage(stats) for stats in self.container_stats()]
        return self._calculated_cpu_usage

    def error(self):
        self._calculated_error = self.feedback() - self.cpu_target
        return self._calculated_error

    def feedback(self):
        if self.is_dead():
            return 0

        total_cpu_usage = sum(self.cpu_usage())
        self._calculated_feedback = total_cpu_usage / self.container_amount
        return self._calculated_feedback

    def stats(self):
        return {
            "status": self.status.value,
            "image": self.image,
            "cpu_target": self.cpu_target,
            "constants": {
                "kp": self.kp,
                "kd": self.kd,
                "ki": self.ki
            },
            "error": self._calculated_error if not self.is_dead() else -self.cpu_target,
            "avg_cpu_usage": self._calculated_feedback if not self.is_dead() else 0,
            "containers": self.container_amount,
            "cpu_usage": self._calculated_cpu_usage if not self.is_dead() else []
        }

    def signal_end(self):
        self._end = True

    def is_dead(self):
        return not self.is_alive() or self.status == Status.DEAD

    def set_constants(self, constants):
        self._constants = constants

    def is_available(self):
        return self.is_alive() and self.status == Status.READY

    def is_initialized(self):
        return not self.status == Status.STARTING

    ###

    def run(self):
        self.initialize()
        self.main()
        self.close()

    def initialize(self):
        print("Initializing...")

        self.create_containers(1)
        # while self.container_list < 1:
        #    pass

        self._status = Status.READY
        print("Client started")

    def close(self):
        print("Closing...")

        self._status = Status.STOPPING
        for container in self.container_list:
            container.kill()

        self.docker_client.containers.prune()
        self._status = Status.DEAD

        print("Client closed")

    def main(self):
        while not self._end:
            n = self.controller()
            self.actuator(n)

    def error_acum(self):
        return self._error_acum

    def controller(self):
        previous_error = self._calculated_error
        error = self.error()
        self._error_acum += error

        change = previous_error - error
        integral = self.error_acum()
        
        MAX_ABS_N = 4  # Simula una banda proporcional
        proportional_gain = self.kp * error 
        gain =  math.copysign(min(MAX_ABS_N, abs(proportional_gain)), proportional_gain) + self.kd * change + self.ki * integral
        return math.ceil(gain)

    def actuator(self, n):
        if n == 0:
            return

        if n < 0:
            self.kill_containers(-n)
        else:
            self.create_containers(n)

    def create_containers(self, n):
        print(f"Instantiating {n} containers...")
        self._status = Status.BUSY
        print("Before: ", self.container_amount)

        for i in range(n):
            self.docker_client.containers.run(self.image, detach=True, ports={'5000/tcp': None})

        print("After: ", self.container_amount)
        self._status = Status.READY
        print(f"Finished instantiating {n} containers.")

    def kill_containers(self, n):
        print("n:", n, '\t', "containers:", self.container_amount)
        containers_to_kill = min(abs(n), self.container_amount - 1)
        #si la cantidad que hay que bajar es mayor o igual a la cantidad de contenedores, dejame solo 1 contenedor corriendo
        if containers_to_kill == 0:
            # containers_to_kill
            return  # TODO fijarse que siempre quede un container levantado

        print(f"Killing {containers_to_kill} containers...")
        self._status = Status.BUSY
        for container in self.container_list[:containers_to_kill]:
            container.kill()

        self.docker_client.containers.prune()
        self._status = Status.READY
        print(f"Finished killing {containers_to_kill} containers...")

    def calculate_cpu_usage(self, stats):
        if self.is_dead():
            return 0

        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]

        cpu_usage = 0
        if cpu_delta > 0 and system_delta > 0:
            cpu_usage = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100

        return cpu_usage

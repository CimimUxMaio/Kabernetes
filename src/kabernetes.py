import math
import threading as th
import docker
import enum

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
        self._last_error = 0
        self._error_acum = 0
        self._end = False
        self._available = False
        self._status = Status.STARTING

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

    def container_stats(self):
        return [ container.stats(stream=False) for container in self.container_list ]

    def cpu_usage(self):
        return [ self.calculate_cpu_usage(stats) for stats in self.container_stats() ]

    def error(self):
        return self.feedback() - self.cpu_target

    def feedback(self):
        if self.is_dead():
            return 0

        total_cpu_usage = sum(self.cpu_usage())
        return total_cpu_usage / len(self.container_list)

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
            "error": self.error(),
            "avg_cpu_usage": self.feedback(),
            "containers": len(self.container_list),
            "cpu_usage": self.cpu_usage()
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
        while len(self.container_list) < 1:
            pass

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
            error = self.error()
            n = self.controler(error)
            self.actuator(n)

    def error_change(self, current):
        return current - self._last_error

    def error_acum(self):
        return self._error_acum

    def controler(self, error):
        self._error_acum += error

        change = self.error_change(error)
        integral = self.error_acum()

        gain = self.kp * error + self.kd * change + self.ki * integral
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
        print("Before: ", len(self.container_list))

        for i in range(n):
            self.docker_client.containers.run(self.image, detach=True)
        
        print("After: ", len(self.container_list))
        self._status = Status.READY
        print(f"Finished instantiating {n} containers.")

    def kill_containers(self, n):
        containers_to_kill = min(abs(n), len(self.container_list) - 1)
        if containers_to_kill == 0:
            return

        print(f"Killing {n} containers...")
        self._status = Status.BUSY
        for container in self.container_list[:n]:
            container.kill()

        self.docker_client.containers.prune()
        self._status = Status.READY
        print(f"Finished killing {n} containers...")
    
    def calculate_cpu_usage(self, stats):
        if self.is_dead():
            return 0

        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]

        cpu_usage = 0
        if cpu_delta > 0 and system_delta > 0:
            cpu_usage = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100

        return cpu_usage
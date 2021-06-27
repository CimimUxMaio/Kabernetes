import math
import threading as th
import docker


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

    def container_stats(self):
        return [ container.stats(stream=False) for container in self.container_list ]

    def cpu_usage(self):
        return [ self.calculate_cpu_usage(stats) for stats in self.container_stats() ]

    def error(self):
        return self.feedback() - self.cpu_target

    def feedback(self):
        total_cpu_usage = sum(self.cpu_usage())
        return total_cpu_usage / len(self.container_list)

    def stats(self):
        return {
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

    def end(self):
        self._end = True

    def set_constants(self, constants):
        self._constants = constants

    def drop_container(self):
        if len(self.container_list) > 1:
            self.kill_containers(1)
    
    def push_container(self):
        self.create_containers(1)

###

    def run(self):
        self.initialize()
        self.main()
        self.close()

    def initialize(self):
        print("Initializing...")

        self.docker_client.containers.run(self.image, detach=True)

        print("Client started")

    def close(self):
        print("Closing...")

        for container in self.container_list:
            container.kill()

        self.docker_client.containers.prune()

        print("Client closed")

    def main(self):
        while not self._end:
            n = self.controler(self.error())
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
            containers_to_kill = min(abs(n), len(self.container_list) - 1)
            if containers_to_kill is 0:
                return

            self.kill_containers(containers_to_kill)
        else:
            self.create_containers(n)

    def create_containers(self, n):
        print(f"Instantiating {n} containers...")
        for i in range(n):
            self.docker_client.containers.run(self.image, detach=True)
        print(f"Finished instantiating {n} containers.")

    def kill_containers(self, n):
        print(f"Killing {n} containers...")
        for container in self.container_list[:n]:
            container.kill()

        self.docker_client.containers.prune()
        print(f"Finished killing {n} containers...")
    
    def calculate_cpu_usage(self, stats):
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]

        cpu_usage = 0
        if cpu_delta > 0 and system_delta > 0:
            cpu_usage = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100

        return cpu_usage
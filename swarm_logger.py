# -*- coding: utf-8 -*-
import docker
import time
import signal
import os
from collector import Collector


class Manager:
    def __init__(self, client):
        self.client = client
        self.log_label_prefix = 'mr5.swarmlogger.'
        self.threads = {}

    def main(self):
        pidfile = open('./swarm-logger.pid', 'w')
        pidfile.write(str(os.getpid()))
        pidfile.close()
        while True:
            try:
                alive_threads = 0
                for container in self.client.containers.list({'status': 'running'}):
                    for label_key in container.labels:
                        if not label_key.startswith(self.log_label_prefix):
                            continue
                        alive_threads += 1
                        if container.id in self.threads:
                            if label_key in self.threads[container.id] \
                                    and self.threads[container.id][label_key].is_alive():
                                continue
                        else:
                            self.threads[container.id] = {}
                        collector_thread = Collector(client=self.client, container=container,
                                                     log_type=container.labels[label_key])
                        collector_thread.setDaemon(True)
                        collector_thread.start()
                        self.threads[container.id][label_key] = collector_thread
                    if container.id not in self.threads:
                        continue
                    for label_key in self.threads[container.id]:
                        if label_key not in container.labels:
                            del self.threads[container.id][label_key]
                            if self.threads[container.id][label_key].is_alive():
                                self.threads[container.id][label_key].stop()
                                alive_threads -= 1
                        if len(self.threads[container.id]) <= 0:
                            del self.threads[container.id]
                print('threads: ' + str(alive_threads) + '/' + str(len(self.threads)))
            except Exception as e:
                print(e)
            time.sleep(1)

    def reopen_log_files(self, signal, frame):
        for container_id in self.threads:
            for label_key in self.threads[container_id]:
                thread = self.threads[container_id][label_key]
                if thread.is_alive():
                    thread.reopen_log_file()


if __name__ == '__main__':
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    manager = Manager(client=client)
    signal.signal(signal.SIGUSR1, manager.reopen_log_files)
    manager.main()

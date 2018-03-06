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
                        if label_key.startswith(self.log_label_prefix):
                            alive_threads += 1
                            if container.id in self.threads and self.threads[container.id].is_alive():
                                continue
                            collector_thread = Collector(client=self.client, container=container,
                                                         log_type=container.labels[label_key])
                            collector_thread.setDaemon(True)
                            collector_thread.start()
                            self.threads[container.id] = collector_thread
                print('threads: ' + str(alive_threads) + '/' + str(len(self.threads)))
            except Exception as e:
                print(e)
            time.sleep(1)

    def reopen_log_files(self, signal, frame):
        for container_id in self.threads:
            thread = self.threads[container_id]
            if thread.is_alive():
                thread.reopen_log_file()


if __name__ == '__main__':
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    manager = Manager(client=client)
    signal.signal(signal.SIGUSR1, manager.reopen_log_files)
    manager.main()

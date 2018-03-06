# -*- coding: utf-8 -*-
import threading
import os
import errno
from docker.errors import APIError
from urllib3.exceptions import HTTPError


class Collector(threading.Thread):
    def __init__(self, client, container, log_type, log_path='/var/log/swarm-logger/'):
        super(Collector, self).__init__()
        self.stop_event = threading.Event()
        self.reopen_event = threading.Event()
        self.client = client
        self.log_path = log_path
        self.log_type = log_type
        self.container = container
        self.file = self.open_container_log_file(container=self.container, log_type=self.log_type)

    def join(self, timeout=None):
        self.stop()
        super(Collector, self).join(timeout)

    def stop(self):
        self.stop_event.set()

    def reopen_log_file(self):
        print('Reopening log file.')
        self.file.close()
        self.file = self.open_container_log_file(container=self.container, log_type=self.log_type)

    def run(self):
        while not self.stop_event.isSet():
            # 通知重新打开日志文件
            if self.reopen_event.isSet():
                self.reopen_log_file()
                self.reopen_event.clear()
            try:
                self.collect_container_logs(container=self.container, log_type=self.log_type)
            except APIError as apiErr:
                if apiErr.is_client_error():
                    self.stop()
                    continue
                print(apiErr)

    def open_container_log_file(self, container, log_type):
        labels = container.labels
        print(labels)
        log_path = self.log_path + labels['com.docker.compose.project'] + '/' + labels['com.docker.compose.service']
        log_file = log_path + '/' + labels['com.docker.compose.service'] + '_' + labels[
            'com.docker.compose.container-number'] + '.' + log_type
        if not os.path.exists(log_path):
            try:
                os.makedirs(log_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        return open(log_file, 'a')

    def collect_container_logs(self, container, log_type):
        while True:
            for line in container.logs(stream=True, stderr=log_type == 'both' or log_type == 'err',
                                       stdout=log_type == 'both' or log_type == 'out'):
                self.file.write(str(line))

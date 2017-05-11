#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from hashlib import sha1
from multiprocessing.managers import BaseManager

from .task import ydl_task, task_status

class share_manager(BaseManager):
    pass


class tasks():
    def __init__(self, opts):
        self._data_ = {}
        self.opts = opts
        share_manager.register('task_status', task_status)
        self.share_manager = share_manager()
        self.share_manager.start()


    def add_info(self, info):
        if 'url' not in info:
            print ('[ERROR] Can not find url in task_info')
            return None

        # Combine default config with the current task_info
        pass

        url = info.get('url')
        tid =  sha1(url.encode()).hexdigest()

        info['tid'] = tid
        self._data_[tid] = {}
        self._data_[tid]['info'] = info
        self._data_[tid]['status'] = None

        return tid


    def get_info(self, tid):
        return self._data_.get(tid).get('info')


    def add_status(self, tid):
        url = self._data_[tid]['info']['url']
        self._data_[tid]['status'] = self.share_manager.task_status(url, self.opts)


    def get_status(self, tid):
        return self._data_.get(tid).get('status')


    def add_object(self, tid, task):
        self._data_[tid]['object'] = task


    def get_object(self, tid):
        return self._data_.get(tid).get('object')


    def list_tasks(self, state='all', exerpt=True):
        state_index = {'all': 0, 'downloading': 1, 'paused': 2, 'finished': 3}
        counter = {'downloading': 0, 'paused': 0, 'finished': 0}

        if state not in state_index:
            return None

        task_list = {}
        for key, val in self._data_.items():
            status = val['status'].get_status()
            cstate = status['state']

            if cstate is state_index['downloading']:
                counter['downloading'] += 1
            elif cstate is state_index['paused']:
                counter['paused'] += 1
            elif cstate is state_index['finished']:
                counter['finished'] += 1

            if state is not 'all' and cstate is not state_index[state]:
                continue

            if exerpt:
                task_list[key] = val['status'].get_exerpt()
            else:
                task_list[key] = val['status'].get_status()

        return task_list, counter


    def query_task(self, tid, exerpt=False):
        if tid not in self._data_:
            return None

        if exerpt:
            return self._data_.get(tid).get('status').get_exerpt()

        status = self._data_.get(tid).get('status').get_status()
        print(status)

        return status


    def delete_task(self, tid):
        task = self._data_.pop(tid)
        status = task.get('status')
        return status


def create_dl_dir(dl_dir):
    # create download dir
    if os.path.exists(dl_dir) and not os.path.isdir(dl_dir):
        print ('[ERROR] The {} exists, but not a valid directory'.format(dl_dir))
        raise Exception('The download directory is not valid')


    if os.path.exists(dl_dir) and not os.access(dl_dir, os.W_OK | os.X_OK):
        print ('[ERROR] The download directory: {} is not writable'.format(dl_dir))
        raise Exception('The download directory is not writable')

    if not os.path.exists(dl_dir):
        os.makedirs(dl_dir)


class ydl_manger():
    def __init__(self, conf=None):
        self.conf = None
        self.tasks = None
        if conf is not None:
            self.load_conf(conf)


    def load_conf(self, conf):
        self.conf = conf
        create_dl_dir(self.conf.download_dir)
        os.chdir(self.conf.download_dir)

        self.tasks = tasks(self.conf)


    def create_task(self, task_info):
        tid = self.tasks.add_info(task_info)
        self.tasks.add_status(tid)

        #  task = ydl_task(tid, self.tasks, self.conf.ydl_opts)
        info = task_info
        status = self.tasks.get_status(tid)
        ydl_opts = self.conf.ydl_opts
        task = ydl_task(info, status, ydl_opts)
        self.tasks.add_object(tid, task)

        return tid


    def start_task(self, tid):
        task = self.tasks.get_object(tid)
        task.start_dl()


    def pause_task(self, tid):
        task = self.tasks.get_object(tid)
        task.pause_dl()


    def resume_task(self, tid):
        task = self.tasks.get_object(tid)
        task.resume_dl()


    def delete_task(self, tid, del_data=False):
        state_index = {'downloading': 1, 'paused': 2, 'finished': 3}
        self.pause_task(tid)
        status = self.tasks.delete_task(tid)
        file_name = status.get_item('file')
        state = status.get_item('state')

        if del_data is True:
            os.remove(file_name)


    def get_task_status(self, tid):
        s = self.tasks.get_status(tid).get_status()
        return s


    def list_tasks(self, state='all', exerpt=True):
        tasks, counter = self.tasks.list_tasks(state=state, exerpt=exerpt)

        return {'tasks': tasks, 'counter': counter}


    def query_task(self, tid, exerpt=False):
        return self.tasks.query_task(tid, exerpt)


    def state_list(self):
        tasks, counter = self.tasks.list_tasks(state='all', exerpt=True)
        return counter


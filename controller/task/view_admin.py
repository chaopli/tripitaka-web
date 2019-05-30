#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 任务管理
@time: 2018/12/26
"""
import math
from controller.task.base import TaskHandler


class TaskAdminHandler(TaskHandler):
    URL = '/task/admin/@task_type'

    def get(self, task_type):
        """ 任务管理 """
        try:
            item_count = self.db.user.count_documents({})
            page_size = int(self.config['pager']['page_size'])
            cur_page = int(self.get_query_argument('page', 1))
            cur_page = math.ceil(item_count / page_size) if math.ceil(item_count / page_size) < cur_page else cur_page
            tasks = self.get_tasks_info_by_type(task_type)
            pager = dict(cur_page=cur_page, item_count=item_count, page_size=page_size)
            self.render('task_admin.html', task_type=task_type, tasks=tasks, pager=pager)
        except Exception as e:
            return self.send_db_error(e, render=True)


class TaskCutStatusHandler(TaskHandler):
    URL = '/task/admin/cut/status'

    def get(self):
        """ 切分任务状态 """

        try:
            item_count = self.db.user.count_documents({})
            page_size = int(self.config['pager']['page_size'])
            cur_page = int(self.get_query_argument('page', 1))
            cur_page = math.ceil(item_count / page_size) if math.ceil(item_count / page_size) < cur_page else cur_page
            tasks = self.get_all_tasks()
            pager = dict(cur_page=cur_page, item_count=item_count, page_size=page_size)
            self.render('task_cut_status.html', tasks=tasks, pager=pager)
        except Exception as e:
            self.send_db_error(e, render=True)


class TaskTextStatusHandler(TaskHandler):
    URL = '/task/admin/text/status'

    def get(self):
        """ 文字任务状态 """

        try:
            item_count = self.db.user.count_documents({})
            page_size = int(self.config['pager']['page_size'])
            cur_page = int(self.get_query_argument('page', 1))
            cur_page = math.ceil(item_count / page_size) if math.ceil(item_count / page_size) < cur_page else cur_page
            tasks = self.get_all_tasks()
            pager = dict(cur_page=cur_page, item_count=item_count, page_size=page_size)
            self.render('task_text_status.html', tasks=tasks, pager=pager)
        except Exception as e:
            self.send_db_error(e, render=True)

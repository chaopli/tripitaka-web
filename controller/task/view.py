#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 任务管理、任务大厅和我的任务
@time: 2018/12/26
"""

import json
from os import path
from controller.task.base import TaskHandler


class TaskLobbyHandler(TaskHandler):
    def show_tasks(self, task_type):
        """ 任务大厅 """

        def pack():
            for t in tasks:
                if t.get(task_type, {}).get('priority'):
                    t['priority'] = t.get(task_type, {}).get('priority')
                    t['pick_url'] = '/task/pick/%s/%s' % (task_type, t['name'])
                    continue
                for k, v in t.get(task_type, {}).items():
                    if v.get('status') in [self.STATUS_OPENED, self.STATUS_RETURNED]:
                        t['priority'] = v.get('priority')
                        t['pick_url'] = '/task/pick/%s/%s' % (task_type, t['name'])
                        continue

        try:
            tasks = self.get_tasks(task_type)
            pack()
            task_name = self.task_types[task_type]['name']
            self.render('task_lobby.html', tasks=tasks, task_type=task_type, task_name=task_name)
        except Exception as e:
            self.send_db_error(e, render=True)

    def get_tasks(self, task_type):
        return self.get_tasks_info_by_type(task_type, [self.STATUS_OPENED, self.STATUS_RETURNED])


class TextProofTaskLobbyHandler(TaskLobbyHandler):
    URL = '/task/lobby/text_proof'

    def get(self):
        """ 文字校对任务大厅 """
        self.show_tasks('text_proof')

    def get_tasks(self, task_type):
        sub_types = self.task_types[task_type]['sub_task_types'].keys()
        not_me = {'%s.%s.user' % (task_type, t): {'$ne': self.current_user['id']} for t in sub_types}
        tasks = self.get_tasks_info_by_type(task_type, [self.STATUS_OPENED, self.STATUS_RETURNED],
                                            set_conditions=lambda cond: cond.update(not_me))
        return tasks


class TextReviewTaskLobbyHandler(TaskLobbyHandler):
    URL = '/task/lobby/text_review'

    def get(self):
        """ 文字审定任务大厅 """
        self.show_tasks('text_review')


class TextHardTaskLobbyHandler(TaskLobbyHandler):
    URL = '/task/lobby/text_hard'

    def get(self):
        """ 难字处理任务大厅 """
        self.show_tasks('text_hard')


class MyTaskHandler(TaskHandler):
    URL = '/task/my/@task_type'

    def get(self, task_type):
        """ 我的任务 """

        try:
            tasks = list(self.get_my_tasks_by_type(task_type))
            task_name = self.task_types[task_type]['name']
            has_sub_tasks = 'sub_task_types' in self.task_types[task_type]

            self.render('my_task.html',
                        tasks=tasks, task_type=task_type, task_name=task_name, has_sub_tasks=has_sub_tasks,
                        task_types=self.task_types, task_statuses=self.task_statuses)
        except Exception as e:
            self.send_db_error(e, render=True)


class TaskAdminHandler(TaskHandler):
    URL = '/task/admin/@task_type'

    def get(self, task_type):
        """ 任务管理 """

        try:
            tasks = self.get_tasks_info_by_type(task_type)
            task_name = self.task_types[task_type]['name']
            has_sub_tasks = 'sub_task_types' in self.task_types[task_type]

            self.render('task_admin.html',
                        tasks=tasks, task_type=task_type, task_name=task_name, has_sub_tasks=has_sub_tasks,
                        task_types=self.task_types, task_statuses=self.task_statuses)
        except Exception as e:
            self.send_db_error(e, render=True)


class TaskCutStatusHandler(TaskHandler):
    URL = '/task/admin/cut/status'

    def get(self):
        """ 切分任务状态 """

        try:
            tasks = self.get_tasks_info()
            self.render('task_cut_status.html', tasks=tasks, task_statuses=self.task_statuses,
                        task_names=self.text_task_names)
        except Exception as e:
            self.send_db_error(e, render=True)


class TaskTextStatusHandler(TaskHandler):
    URL = '/task/admin/text/status'

    def get(self):
        """ 文字任务状态 """

        try:
            tasks = self.get_tasks_info()
            self.render('task_text_status.html', tasks=tasks, task_statuses=self.task_statuses,
                        task_names=self.cut_task_names)
        except Exception as e:
            self.send_db_error(e, render=True)


class LobbyBlockCutProofHandler(TaskLobbyHandler):
    URL = '/task/lobby/block_cut_proof'

    def get(self):
        """ 任务大厅-栏切分校对 """
        self.show_tasks('block_cut_proof')


class LobbyColumnCutProofHandler(TaskLobbyHandler):
    URL = '/task/lobby/column_cut_proof'

    def get(self):
        """ 任务大厅-列切分校对 """
        self.show_tasks('column_cut_proof')


class LobbyCharCutProofHandler(TaskLobbyHandler):
    URL = '/task/lobby/char_cut_proof'

    def get(self):
        """ 任务大厅-字切分校对 """
        self.show_tasks('char_cut_proof')


class LobbyBlockCutReviewHandler(TaskLobbyHandler):
    URL = '/task/lobby/block_cut_review'

    def get(self):
        """ 任务大厅-栏切分审定 """
        self.show_tasks('block_cut_review')


class LobbyColumnCutReviewHandler(TaskLobbyHandler):
    URL = '/task/lobby/column_cut_review'

    def get(self):
        """ 任务大厅-列切分审定 """
        self.show_tasks('column_cut_review')


class LobbyCharCutReviewHandler(TaskLobbyHandler):
    URL = '/task/lobby/char_cut_review'

    def get(self):
        """ 任务大厅-字切分审定 """
        self.show_tasks('char_cut_review')


class CutDetailBaseHandler(TaskHandler):
    def enter(self, box_type, stage, name):
        def handle_response(body):
            try:
                page = self.db.page.find_one(dict(name=name))
                if not page:
                    return self.render('_404.html')

                self.render('text_proof.html', page=page,
                            readonly=body.get('name') != name,
                            title='切分校对' if stage == 'proof' else '切分审定',
                            get_img=self.get_img,
                            box_type=box_type, stage=stage, task_type=task_type, task_name=task_name)
            except Exception as e:
                self.send_db_error(e, render=True)

        task_type = '%s_cut_%s' % (box_type, stage)
        task_name = '%s切分' % dict(block='栏', column='列', char='字')[box_type]
        self.call_back_api('/api/pick/{0}/{1}'.format(task_type, name), handle_response)

    def get_img(self, name):
        cfg = self.application.config
        if 'page_codes' not in cfg:
            try:
                cfg['page_codes'] = json.load(open(path.join(self.application.BASE_DIR, 'page_codes.json')))
            except OSError:
                cfg['page_codes'] = {}
        code = cfg['page_codes'].get(name)
        if code:
            base_url = 'http://tripitaka-img.oss-cn-beijing.aliyuncs.com/page'
            sub_dirs = '/'.join(name.split('_')[:-1])
            url = '/'.join([base_url, sub_dirs, name + '_' + code + '.jpg'])
            return url + '?x-oss-process=image/resize,m_lfit,h_300,w_300'

        return '/static/img/{0}/{1}.jpg'.format(name[:2], name)


class CutProofDetailHandler(CutDetailBaseHandler):
    URL = '/task/do/@box-type_cut_proof/@task_id'

    def get(self, box_type, name):
        """ 进入切分校对页面 """
        self.enter(box_type, 'proof', name)


class CutReviewDetailHandler(CutDetailBaseHandler):
    URL = '/task/do/@box-type_cut_review/@task_id'

    def get(self, box_type, name):
        """ 进入切分审定页面 """
        self.enter(box_type, 'review', name)


class CharProofDetailHandler(TaskHandler):
    URL = '/task/do/text_proof/@num/@task_id'

    def get(self, name=''):
        """ 进入文字校对 """
        try:
            page = self.db.page.find_one(dict(name=name)) or dict(name='?')
            if not page:
                return self.render('_404.html')
            self.render('text_proof.html', page=page,
                        readonly=page.get('text_proof_user') != self.current_user['id'])
        except Exception as e:
            self.send_db_error(e, render=True)


class CharReviewDetailHandler(TaskHandler):
    URL = '/task/do/text_review/@num/@task_id'

    def get(self, name=''):
        """ 进入文字校对 """
        try:
            page = self.db.page.find_one(dict(name=name)) or dict(name='?')
            if not page:
                return self.render('_404.html')
            self.render('text_review.html', page=page,
                        readonly=page.get('text_proof_user') != self.current_user['id'])
        except Exception as e:
            self.send_db_error(e, render=True)

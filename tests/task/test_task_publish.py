#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tests.users as u
from tests.testcase import APITestCase
from controller.task.base import TaskHandler as Th


class TestTaskPublish(APITestCase):

    def setUp(self):
        super(TestTaskPublish, self).setUp()
        # 创建几个专家用户（权限足够），用于审校流程的测试
        self.add_first_user_as_admin_then_login()
        self.add_users_by_admin(
            [dict(email=r[0], name=r[2], password=r[1]) for r in [u.expert1, u.expert2, u.expert3]], '切分专家,文字专家'
        )
        # 初始化任务状态
        self.revert()

    def tearDown(self):
        super(TestTaskPublish, self).tearDown()

    def assert_status(self, pages, response, task_type_status_maps):
        for task_type, status in task_type_status_maps.items():
            data = response.get('data', {})
            _pages = data.get(status, []) or data.get(task_type, {}).get(status, [])
            self.assertEqual(set(pages), set(_pages))

    def test_publish_tasks(self):
        """ 测试发布审校任务 """
        self.add_first_user_as_admin_then_login()

        """ 测试异常情况 """
        # 页面为空
        r = self.parse_response(self.publish(dict(task_type='block_cut_proof', pages='')))
        self.assertIn('pages', r['error'])

        # 任务类型有误
        pages = 'GL_1056_5_6,JX_165_7_12'
        r = self.parse_response(self.publish(dict(task_type='error_task_type', pages=pages)))
        self.assertIn('task_type', r['error'])

        # 优先级有误，必须为1/2/3
        r = self.parse_response(self.publish(dict(task_type='block_cut_proof', pages=pages, priority='高')))
        self.assertIn('priority', r['error'])

        for task_type in [
            'block_cut_proof', 'block_cut_review',
            'column_cut_proof', 'column_cut_review',
            'char_cut_proof', 'char_cut_review',
            'text_proof_1', 'text_proof_2', 'text_proof_3', 'text_review'
        ]:
            pages_un_existed = ['GL_not_existed_1', 'JX_not_existed_2']
            r = self.parse_response(self.publish(dict(task_type=task_type, pages=','.join(pages_un_existed))))
            self.assert_status(pages_un_existed, r, {task_type: 'un_existed'})

            # 测试未就绪的页面
            pages_un_ready = ['GL_1056_5_6', 'JX_165_7_12', 'JX_165_7_30', 'JX_165_7_75', 'JX_165_7_87']
            self.set_task_status({task_type: Th.STATUS_UNREADY}, pages_un_ready)
            r = self.parse_response(self.publish(dict(task_type=task_type, pages=','.join(pages_un_ready))))
            self.assert_status(pages_un_ready, r, {task_type: 'un_ready'})

            # 测试已就绪的页面
            pages_ready = ['QL_25_16', 'QL_25_313', 'QL_25_416', 'QL_25_733', 'YB_22_346', 'YB_22_389']
            self.set_task_status({task_type: Th.STATUS_READY}, pages_ready)
            r = self.parse_response(self.publish(dict(task_type=task_type, pages=','.join(pages_ready))))
            status = 'published' if 'proof' in task_type else 'pending'
            self.assert_status(pages_ready, r, {task_type: status})

            # 测试已发布的页面
            pages_published_before = ['YB_22_916', 'YB_22_995']
            self.set_task_status({task_type: Th.STATUS_OPENED}, pages_published_before)
            r = self.parse_response(self.publish(dict(task_type=task_type, pages=','.join(pages_published_before))))
            self.assert_status(pages_published_before, r, {task_type: 'published_before'})

            # 组合测试
            all_pages = pages_un_existed + pages_un_ready + pages_ready + pages_published_before
            self.set_task_status({task_type: Th.STATUS_UNREADY}, pages_un_ready)
            self.set_task_status({task_type: Th.STATUS_READY}, pages_ready)
            self.set_task_status({task_type: Th.STATUS_OPENED}, pages_published_before)
            r = self.parse_response(self.publish(dict(task_type=task_type, pages=','.join(all_pages))))
            self.assert_status(pages_un_existed, r, {task_type: 'un_existed'})
            self.assert_status(pages_un_ready, r, {task_type: 'un_ready'})
            self.assert_status(pages_ready, r, {task_type: status})
            self.assert_status(pages_published_before, r, {task_type: 'published_before'})

            # 还原页面状态
            self.set_task_status({task_type: Th.STATUS_READY}, pages_un_ready)
            self.set_task_status({task_type: Th.STATUS_READY}, pages_published_before)

    def test_publish_tasks_with_pre_tasks(self):
        """ 测试发布带前置任务的任务 """
        page_names = ['YB_22_713', 'YB_22_759', 'YB_22_816']
        for t, pre in self.pre_tasks.items():
            if pre:
                self.set_task_status({t: Th.STATUS_READY}, page_names)
                if isinstance(pre, list):
                    pre = pre[0]
                self.set_task_status({pre: Th.STATUS_READY}, page_names)
                r = self.parse_response(self.publish(dict(task_type=t, pages=','.join(page_names))))
                pending = r.get('data', {}).get('pending')
                self.assertEqual(set(page_names), set(pending))

    def test_publish_tasks_file(self):
        """ 测试以文件方式发布审校任务 """
        self.add_first_user_as_admin_then_login()
        # 创建文件
        pages = ['GL_1056_5_6', 'JX_165_7_12']
        self.set_task_status({'block_cut_proof': 'ready'}, pages)
        filename = os.path.join(self._app.BASE_DIR, 'static', 'upload', 'file2upload.txt')
        with open(filename, 'w') as f:
            for page in pages:
                f.write(page + '\n')
        self.assertTrue(os.path.exists(filename))

        # 测试正常发布
        task_type = 'block_cut_proof'
        body = dict(task_type=task_type, priority=1, pre_tasks=self.pre_tasks.get(task_type))
        r = self.parse_response(self.fetch('/api/task/publish_file', files=dict(txt_file=filename), body=body))
        self.assertEqual(set(r.get('published')), set(pages))

        # 测试任务类型有误
        task_type = 'error_task_type'
        body = dict(task_type=task_type, priority=1, pre_tasks=self.pre_tasks.get(task_type))
        r = self.parse_response(self.fetch('/api/task/publish_file', files=dict(txt_file=filename), body=body))
        self.assertIn('task_type', r['error'])

    def test_publish_many_tasks(self, size=10000):
        """ 测试发布大规模任务 """
        for task_type in [
            'block_cut_proof', 'block_cut_review',
        ]:
            pages = self._app.db.page.find({}, {'name': 1}).limit(size)
            page_names = [page['name'] for page in pages]
            self.set_task_status({task_type: Th.STATUS_READY}, page_names)
            r = self.parse_response(self.publish(dict(task_type=task_type, pages=','.join(page_names))))
            status = 'published' if 'proof' in task_type else 'pending'
            self.assertIn(status, r['data'])

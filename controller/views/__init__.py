#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 在 controller.views 包实现页面响应类，生成前端页面，modules 为重用网页片段的渲染类

from . import modules, home, tripitaka as t
from controller.user import view
from controller.task import view

handlers = [home.HomeHandler,
            view.UserLoginHandler, view.UserRegisterHandler,
            view.UsersAdminHandler, view.UserRolesHandler, view.UserStatisticHandler, view.UserProfileHandler,
            view.LobbyBlockCutProofHandler, view.LobbyColumnCutProofHandler, view.LobbyCharCutProofHandler,
            view.LobbyBlockCutReviewHandler, view.LobbyColumnCutReviewHandler, view.LobbyCharCutReviewHandler,
            view.CharProofDetailHandler, view.CutProofDetailHandler, view.CutReviewDetailHandler,
            view.CharReviewDetailHandler,
            view.TaskCutStatusHandler, view.TaskTextStatusHandler,
            view.TextProofTaskLobbyHandler, view.TextReviewTaskLobbyHandler, view.TextHardTaskLobbyHandler,
            view.TaskAdminHandler, view.MyTaskHandler,
            t.RsTripitakaHandler, t.TripitakaListHandler, t.TripitakaHandler, t.DataTripitakaHandler,
            t.DataEnvelopHandler, t.DataVolumeHandler, t.DataSutraHandler, t.DataReelHandler, t.DataPageHandler,
            ]

modules = {'CommonLeft': modules.CommonLeft, 'CommonHead': modules.CommonHead,
           'Pager': modules.Pager}

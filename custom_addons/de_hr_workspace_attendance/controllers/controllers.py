# -*- coding: utf-8 -*-
# from odoo import http


# class DeHrWorkspaceAttendance(http.Controller):
#     @http.route('/de_hr_workspace_attendance/de_hr_workspace_attendance', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_hr_workspace_attendance/de_hr_workspace_attendance/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_hr_workspace_attendance.listing', {
#             'root': '/de_hr_workspace_attendance/de_hr_workspace_attendance',
#             'objects': http.request.env['de_hr_workspace_attendance.de_hr_workspace_attendance'].search([]),
#         })

#     @http.route('/de_hr_workspace_attendance/de_hr_workspace_attendance/objects/<model("de_hr_workspace_attendance.de_hr_workspace_attendance"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_hr_workspace_attendance.object', {
#             'object': obj
#         })

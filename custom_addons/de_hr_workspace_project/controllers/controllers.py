# -*- coding: utf-8 -*-
# from odoo import http


# class DeHrWorkspaceProject(http.Controller):
#     @http.route('/de_hr_workspace_project/de_hr_workspace_project', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_hr_workspace_project/de_hr_workspace_project/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_hr_workspace_project.listing', {
#             'root': '/de_hr_workspace_project/de_hr_workspace_project',
#             'objects': http.request.env['de_hr_workspace_project.de_hr_workspace_project'].search([]),
#         })

#     @http.route('/de_hr_workspace_project/de_hr_workspace_project/objects/<model("de_hr_workspace_project.de_hr_workspace_project"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_hr_workspace_project.object', {
#             'object': obj
#         })

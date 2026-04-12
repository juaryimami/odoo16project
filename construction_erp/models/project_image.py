# -*- coding: utf-8 -*-
from odoo import models, fields

class ProjectImage(models.Model):
    _name = 'construction.project.image'
    _description = 'Project Progress Image'

    name = fields.Char("Title", required=True)
    project_id = fields.Many2one('project.project', "Project", required=True, ondelete='cascade')
    image = fields.Image("Image", max_width=1920, max_height=1920, required=True)
    date = fields.Date("Date Taken", default=fields.Date.context_today)
    notes = fields.Text("Description")

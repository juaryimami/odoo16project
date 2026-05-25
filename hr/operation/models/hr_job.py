from odoo import models, fields

class HrJob(models.Model):
    _inherit = 'hr.job'

    project_id = fields.Many2one('agent.project', string="Project")

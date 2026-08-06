# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectMasterPlanSummary(models.Model):
    _name = 'project.master.plan.summary'
    _description = 'Grouped Project Plan Summary'
    _order = 'item_type'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    item_type = fields.Char(string='Item Type')
    total_budget = fields.Monetary(string='Total Estimated Budget')
    actual_spent = fields.Monetary(string='Actual Spend')
    phases = fields.Char(string='Phases of Estimated')
    variation_amount = fields.Monetary(string='Total Variation')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id')

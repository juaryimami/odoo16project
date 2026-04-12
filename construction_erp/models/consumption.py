# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionConsumption(models.Model):
    _name = 'construction.consumption'
    _description = 'Daily Material Consumption Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, default='New')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, tracking=True)
    user_id = fields.Many2one('res.users', string='Reported By', default=lambda self: self.env.user)
    daily_log_id = fields.Many2one('construction.daily.log', string='Daily Log')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated')
    ], string='Status', default='draft', tracking=True)

    line_ids = fields.One2many('construction.consumption.line', 'consumption_id', string='Materials Consumed')

    def action_validate(self):
        for record in self:
            record.state = 'validated'

class ConstructionConsumptionLine(models.Model):
    _name = 'construction.consumption.line'
    _description = 'Consumption Line'

    consumption_id = fields.Many2one('construction.consumption', string='Consumption Ref', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True)
    quantity = fields.Float(string='Quantity Used', required=True, default=1.0)
    notes = fields.Char(string='Notes')

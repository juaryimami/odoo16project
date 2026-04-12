# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ConstructionDailyLog(models.Model):
    _name = 'construction.daily.log'
    _description = 'Construction Daily Progress Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Log Reference', compute='_compute_name', store=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    task_id = fields.Many2one('project.task', string='Construction Phase', domain="[('project_id', '=', project_id)]", tracking=True)
    supervisor_id = fields.Many2one('res.users', string='Supervisor', default=lambda self: self.env.user)
    
    labor_count = fields.Integer(string='Total Labor Count on Site', compute='_compute_labor_count', store=True)
    skilled_labor_count = fields.Integer(string='Skilled Labor', tracking=True)
    unskilled_labor_count = fields.Integer(string='Unskilled Labor', tracking=True)
    
    weather_conditions = fields.Selection([
        ('sunny', 'Sunny / Clear'),
        ('cloudy', 'Cloudy'),
        ('rain', 'Rain'),
        ('snow', 'Snow / Extreme')
    ], string='Weather Conditions')
    
    equipment_notes = fields.Text(string='Equipment Usage Notes')
    issues_notes = fields.Text(string='Issues / Delays')
    consumption_ids = fields.One2many('construction.consumption', 'daily_log_id', string='Material Consumption Reports')
    visitor_ids = fields.One2many('construction.site.visitor', 'daily_log_id', string='Site Visitors')

    @api.depends('skilled_labor_count', 'unskilled_labor_count')
    def _compute_labor_count(self):
        for log in self:
            log.labor_count = log.skilled_labor_count + log.unskilled_labor_count

class ConstructionSiteVisitor(models.Model):
    _name = 'construction.site.visitor'
    _description = 'Site Visitor Registry'

    daily_log_id = fields.Many2one('construction.daily.log', string='Daily Log', ondelete='cascade')
    name = fields.Char(string='Visitor Name', required=True)
    company = fields.Char(string='Company / Organization')
    reason = fields.Char(string='Reason for Visit')
    time_in = fields.Float(string='Time In')
    time_out = fields.Float(string='Time Out')

    @api.depends('date', 'project_id')
    def _compute_name(self):
        for log in self:
            if log.date and log.project_id:
                log.name = f"Log: {log.project_id.name} - {log.date}"
            else:
                log.name = "New Log"

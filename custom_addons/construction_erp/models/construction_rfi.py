# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionRFI(models.Model):
    _name = 'construction.rfi'
    _description = 'Request for Information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    phase_id = fields.Many2one('project.task', string='Phase', domain="[('project_id', '=', project_id)]", tracking=True)
    
    subject = fields.Char(string='Subject', required=True, tracking=True)
    question = fields.Html(string='Question', required=True)
    response = fields.Html(string='Consultant Response', tracking=True)
    
    requested_from_id = fields.Many2one('res.partner', string='Requested From', tracking=True, help="Consultant or Engineer being asked")
    date = fields.Date(string='Date Requested', default=fields.Date.context_today, required=True)
    due_date = fields.Date(string='Due Date', tracking=True)
    response_date = fields.Date(string='Response Date', readonly=True)
    
    aging_days = fields.Integer(string='Aging (Days)', compute='_compute_aging', store=True)
    
    impact_cost = fields.Boolean(string='Impact on Cost', tracking=True)
    impact_schedule = fields.Boolean(string='Impact on Schedule', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('responded', 'Responded/Resolved'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.rfi') or _('New')
        return super(ConstructionRFI, self).create(vals_list)

    @api.depends('date', 'response_date', 'state')
    def _compute_aging(self):
        today = fields.Date.context_today(self)
        for rfi in self:
            if rfi.state in ['responded', 'closed'] and rfi.response_date:
                rfi.aging_days = (rfi.response_date - rfi.date).days
            else:
                rfi.aging_days = (today - rfi.date).days

    def action_send(self):
        self.ensure_one()
        self.write({'state': 'sent'})

    def action_respond(self):
        self.ensure_one()
        self.write({
            'state': 'responded',
            'response_date': fields.Date.context_today(self)
        })

    def action_close(self):
        self.ensure_one()
        self.write({'state': 'closed'})

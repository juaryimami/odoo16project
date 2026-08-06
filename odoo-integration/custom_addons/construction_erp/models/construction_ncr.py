# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionNCR(models.Model):
    _name = 'construction.ncr'
    _description = 'Non-Conformance Report (NCR)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='NCR Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    inspection_id = fields.Many2one('construction.inspection', string='Source Inspection', readonly=True)
    
    date_identified = fields.Date(string='Date Identified', default=fields.Date.context_today, required=True)
    non_conformance_desc = fields.Text(string='Description of Non-Conformance', required=True)
    
    root_cause = fields.Text(string='Root Cause Analysis')
    corrective_action = fields.Text(string='Proposed Corrective Action')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('repair', 'In Repair'),
        ('verified', 'Verified / Repaired'),
        ('closed', 'Closed'),
        ('void', 'Void')
    ], string='Status', default='draft', tracking=True)
    
    responsible_id = fields.Many2one('res.users', string='Responsible Person', tracking=True)
    target_date = fields.Date(string='Target Completion Date')
    completion_date = fields.Date(string='Actual Completion Date')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.ncr') or _('New')
        return super(ConstructionNCR, self).create(vals_list)

    def action_open(self):
        self.write({'state': 'open'})

    def action_repair(self):
        self.write({'state': 'repair'})

    def action_verify(self):
        self.write({'state': 'verified', 'completion_date': fields.Date.today()})

    def action_close(self):
        self.write({'state': 'closed'})

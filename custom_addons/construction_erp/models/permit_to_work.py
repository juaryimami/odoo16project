# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionPermitToWork(models.Model):
    _name = 'construction.permit.work'
    _description = 'Permit to Work (PTW)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Permit No', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    permit_type = fields.Selection([
        ('hot_work', 'Hot Work (Welding/Cutting)'),
        ('height_work', 'Work at Height'),
        ('confined_space', 'Confined Space Entry'),
        ('excavation', 'Excavation / Trenching'),
        ('electrical', 'Electrical Work'),
        ('lifting', 'Critical Lifting')
    ], string='Permit Type', required=True, tracking=True)
    
    applicant_id = fields.Many2one('res.users', string='Applicant (Issuer)', default=lambda self: self.env.user, required=True)
    receiver_id = fields.Many2one('res.partner', string='Permit Receiver (Contractor/Lead)', required=True)
    
    start_datetime = fields.Datetime(string='Valid From', required=True, default=fields.Datetime.now)
    end_datetime = fields.Datetime(string='Valid To', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    hazards_identified = fields.Text(string='Identified Hazards')
    precautions_required = fields.Text(string='Precautions & PPE Required')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.permit.work') or _('New')
        return super(ConstructionPermitToWork, self).create(vals_list)

    def action_request(self):
        self.write({'state': 'requested'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

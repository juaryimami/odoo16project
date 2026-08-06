# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionSubmittal(models.Model):
    _name = 'construction.submittal'
    _description = 'Technical Submittal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    phase_id = fields.Many2one('project.task', string='Phase', domain="[('project_id', '=', project_id)]", tracking=True)
    
    title = fields.Char(string='Submittal Title', required=True, tracking=True)
    submittal_type = fields.Selection([
        ('drawing', 'Shop Drawing'),
        ('material', 'Material Sample'),
        ('data', 'Technical Data Sheet'),
        ('sample', 'Mockup/Sample'),
        ('other', 'Other')
    ], string='Type', required=True, tracking=True)
    
    revision = fields.Integer(string='Revision', default=0, tracking=True)
    
    reviewer_id = fields.Many2one('res.partner', string='Reviewer', help="Consultant/Engineer responsible for approval")
    date_submitted = fields.Date(string='Submission Date', default=fields.Date.context_today)
    date_response = fields.Date(string='Response Date', readonly=True)
    
    approval_status = fields.Selection([
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('approved_noted', 'Approved as Noted'),
        ('resubmit', 'Revised & Resubmit'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', tracking=True)
    
    notes = fields.Text(string='Technical Remarks')
    attachment_ids = fields.Many2many('ir.attachment', string='Technical Documents')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.submittal') or _('New')
        return super(ConstructionSubmittal, self).create(vals_list)

    def action_approve(self):
        self.ensure_one()
        self.write({
            'approval_status': 'approved',
            'date_response': fields.Date.context_today(self)
        })

    def action_reject(self):
        self.ensure_one()
        self.write({
            'approval_status': 'rejected',
            'date_response': fields.Date.context_today(self)
        })
    
    def action_resubmit(self):
        self.ensure_one()
        self.write({
            'approval_status': 'resubmit',
            'date_response': fields.Date.context_today(self)
        })

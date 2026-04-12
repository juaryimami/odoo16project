# -*- coding: utf-8 -*-
from odoo import models, fields

class ProjectDocument(models.Model):
    _name = 'construction.document'
    _description = 'Construction Document Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Document Name', required=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project', required=True, ondelete='cascade')
    document_type = fields.Selection([
        ('blueprint', 'Architectural Blueprint'),
        ('contract', 'Subcontractor Agreement'),
        ('permit', 'City Permit'),
        ('financial', 'Financial Record'),
        ('photo', 'Site Photo'),
        ('other', 'Other')
    ], string='Document Type', required=True, default='other', tracking=True)
    
    attachment_file = fields.Binary(string='File', required=True, attachment=True)
    file_name = fields.Char(string='File Name')
    upload_date = fields.Date(string='Upload Date', default=fields.Date.context_today, required=True)
    notes = fields.Text(string='Description / Notes')

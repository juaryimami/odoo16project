# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrPolicyTemplate(models.Model):
    _name = 'hr.policy.template'
    _description = 'HR Policy Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Policy Title', required=True, tracking=True)
    active = fields.Boolean(default=True)
    content_type = fields.Selection([
        ('text', 'Rich Text Editor'),
        ('file', 'File Upload (PDF/Word)')
    ], string='Content Type', default='text', required=True)
    
    body_html = fields.Html(string='Policy Content')
    attachment = fields.Binary(string='File Attachment')
    attachment_name = fields.Char(string='File Name')
    
    target_type = fields.Selection([
        ('all', 'All Active Employees'),
        ('department', 'Specific Departments'),
        ('specific', 'Specific Employees')
    ], string='Target Type', default='all', required=True, tracking=True)
    
    department_ids = fields.Many2many('hr.department', string='Target Departments')
    employee_ids = fields.Many2many('hr.employee', string='Target Employees')
    
    current_version_id = fields.Many2one('hr.policy.version', string='Current Version', readonly=True)
    version_ids = fields.One2many('hr.policy.version', 'template_id', string='Versions')
    
    def action_publish_wizard(self):
        self.ensure_one()
        return {
            'name': _('Publish New Version'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.policy.publish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_version_num': self.current_version_id and _('%s (New)') % self.current_version_id.version_num or 'v1.0',
            }
        }

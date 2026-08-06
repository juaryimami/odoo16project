# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrPolicyVersion(models.Model):
    _name = 'hr.policy.version'
    _description = 'HR Policy Version'
    _order = 'published_date desc, id desc'

    template_id = fields.Many2one('hr.policy.template', string='Policy Template', required=True, ondelete='cascade')
    version_num = fields.Char(string='Version Number', required=True)
    published_date = fields.Datetime(string='Published Date', default=fields.Datetime.now, required=True)
    
    # Snapshot of the policy at the time of publishing
    content_type = fields.Selection([
        ('text', 'Rich Text Editor'),
        ('file', 'File Upload (PDF/Word)')
    ], string='Content Type', required=True)
    body_html = fields.Html(string='Policy Content (Snapshot)')
    attachment = fields.Binary(string='File Attachment (Snapshot)')
    attachment_name = fields.Char(string='File Name')
    
    is_major = fields.Boolean(string='Is Major Update', help="If true, employees will be required to sign this new version again.")
    
    attestation_ids = fields.One2many('hr.policy.attestation', 'version_id', string='Attestations')
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.template_id.name} ({record.version_num})"
            result.append((record.id, name))
        return result

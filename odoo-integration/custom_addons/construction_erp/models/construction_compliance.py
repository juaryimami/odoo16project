# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date

class ConstructionCompliance(models.Model):
    _name = 'construction.compliance'
    _description = 'Master Project Compliance & Legal Permits'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Permit / Document Name', required=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project Allocation', required=True, ondelete='cascade', tracking=True)
    
    compliance_type = fields.Selection([
        ('building_permit', 'Structural Building Approval'),
        ('safety', 'OSHA / Safety Certification'),
        ('environmental', 'Environmental Clearance'),
        ('insurance', 'Liability Insurance Policy'),
        ('legal', 'Zoning / Land Rights'),
        ('other', 'Other Parameter')
    ], string='Classification Type', default='building_permit', required=True, tracking=True)
    
    issuing_authority = fields.Char(string='Issuing Authority', tracking=True)
    issue_date = fields.Date(string='Official Issue Date')
    expiration_date = fields.Date(string='Expiration Deadline', required=True, tracking=True)
    
    document_file = fields.Binary(string='Digital Copy')
    file_name = fields.Char(string='File Name')
    
    status = fields.Selection([
        ('pending', 'Pending Final Approval'),
        ('active', 'Active & Legally Valid'),
        ('expired', 'Critical: EXPIRED')
    ], string='Current Legal Status', default='pending', tracking=True)

    @api.model
    def _cron_check_compliance_expiry(self):
        """ Nightly autonomous loop downgrading any passed expiration dates immediately into EXPIRED states triggering alerts """
        expired_documents = self.search([
            ('status', 'in', ['active', 'pending']),
            ('expiration_date', '<', fields.Date.today())
        ])
        
        for doc in expired_documents:
            doc.write({'status': 'expired'})
            
            # Post a priority alert instantly to the Master Project dashboard ensuring immediate executive visibility
            alert_message = f"""
                <div class="alert alert-danger" role="alert">
                    <h4 class="alert-heading"><i class="fa fa-warning"></i> CRITICAL LEGAL EXPIRATION ALERT</h4>
                    <p>The Compliance Document <b>{doc.name}</b> (Type: <i>{doc.compliance_type}</i>) issued by <b>{doc.issuing_authority}</b> has officially expired today.</p>
                    <hr/>
                    <p class="mb-0">Please secure a renewed permit immediately to prevent operational interruptions.</p>
                </div>
            """
            doc.project_id.message_post(body=alert_message, subject="Legal Expiration")

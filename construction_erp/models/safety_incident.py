# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionSafetyIncident(models.Model):
    _name = 'construction.safety.incident'
    _description = 'Site Safety Incident Log'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Incident Ref', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    date = fields.Date(string='Incident Date', default=fields.Date.context_today, required=True, tracking=True)
    
    incident_type = fields.Selection([
        ('near_miss', 'Near Miss'),
        ('first_aid', 'First Aid'),
        ('medical_treatment', 'Medical Treatment'),
        ('lost_time', 'Lost Time Injury (LTI)'),
        ('fatality', 'Fatality'),
        ('property_damage', 'Property Damage'),
        ('environmental', 'Environmental Incident')
    ], string='Incident Type', required=True, tracking=True)
    
    severity = fields.Selection([
        ('low', 'Low / Minor'),
        ('medium', 'Medium'),
        ('high', 'High / Critical'),
        ('extreme', 'Extreme / Catastrophic')
    ], string='Severity', required=True, tracking=True, default='medium')
    
    state = fields.Selection([
        ('reported', 'Reported'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], string='Status', default='reported', tracking=True)
    
    description = fields.Text(string='Description of Event', required=True)
    root_cause = fields.Text(string='Root Cause Analysis')
    corrective_action = fields.Text(string='Corrective Actions Taken')
    
    location_on_site = fields.Char(string='Specific Location on Site')
    involved_party = fields.Char(string='Parties Involved')
    
    witness_notes = fields.Text(string='Witness statements')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.safety.incident') or _('New')
        records = super(ConstructionSafetyIncident, self).create(vals_list)
        
        # Automated Safety Alert for High Severity
        for record in records:
            if record.severity in ['high', 'extreme']:
                record._trigger_safety_alert()
        return records

    def _trigger_safety_alert(self):
        """ Notify PM and Site Manager immediately for critical incidents """
        self.ensure_one()
        msg = _("🚨 CRITICAL SAFETY INCIDENT [%s] at %s\nType: %s\nSeverity: %s\nDetails: %s") % (
            self.name, self.project_id.name, self.incident_type, self.severity, self.description[:100]
        )
        
        # Notify Project Manager
        if self.project_id.user_id:
            self.notify_contact(self.project_id.user_id.partner_id, msg, title="Critical Safety Alert")
        
        # Notify Site Manager
        if self.project_id.site_manager_id:
             self.notify_contact(self.project_id.site_manager_id, msg, title="Critical Safety Alert")

    def action_investigate(self):
        self.write({'state': 'investigating'})

    def action_resolve(self):
        self.write({'state': 'resolved'})

    def action_close(self):
        self.write({'state': 'closed'})

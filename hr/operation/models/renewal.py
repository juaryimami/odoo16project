import logging

from odoo.exceptions import ValidationError
from odoo import models, fields, api

from datetime import timedelta, date

_logger = logging.getLogger(__name__)
from odoo import models, fields, api



class AgentProjectRenewal(models.Model):
    _name = 'agent.project.renewal'
    _description = 'Project Renewal'

    project_id = fields.Many2one('agent.project', string='Project', required=True)
    renewal_start_date = fields.Date(string='Renewal Start Date', required=True)
    renewal_end_date = fields.Date(string='Renewal End Date', required=True)
    updated_price = fields.Float(string='Updated Price')
    renewal_number = fields.Integer(string='Renewal Number', compute='_compute_renewal_number', store=True)


    def renew_project(self):
        self.send_project_renewal_email()
        for rec in self:
            rec.project_id.write({
                'start_date':rec.renewal_start_date,
                'end_date':rec.renewal_end_date,
                'renewal_date':date.today(),
            })

    def send_project_renewal_email(self):
        """Send notification email when a project is created."""
        try:
            users = self.env['hr.employee'].search([('job_id.name', 'in', ["Managing Director","HR Manager","Finance Manager","Section Head"])])
            for ch in users:
                location_names = [agent.location_id.name for agent in self.project_id.agent_ids if agent.location_id]
                self.env['mail.mail'].create({
                    'subject': 'ERP System Notification: Contract Amended',
                    'email_from': ch.company_id.email,
                    'email_to': ch.work_email,  # Assuming Via is a user and has an email address
                    'body_html': f"The contract for the provision of {self.project_id.contract_name} to {self.project_id.client} at {', '.join(location_names)} is amended as of   {self.renewal_end_date} <br/><br/>Best regards!!",
                }).send()

        except Exception as e:
            _logger.error('Error sending email: %s', e)



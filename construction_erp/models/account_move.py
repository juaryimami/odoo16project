# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    job_order_id = fields.Many2one('construction.job.order', string='Linked Job Order')
    inspection_id = fields.Many2one('construction.inspection', string='Required Inspection')
    installment_line_id = fields.Many2one('real_estate.installment.line', string='Linked Installment Line')
    project_id = fields.Many2one('project.project', string='Construction Project', help="The construction project this document belongs to.")
    lifecycle_id = fields.Many2one('construction.lifecycle', related='project_id.lifecycle_id')
    last_reminder_sent = fields.Date(string='Last Reminder Date', copy=False)
    reminder_count = fields.Integer(string='Reminders Sent', default=0, copy=False)
    cpr_id = fields.Many2one('construction.cpr', string='Linked CPR', readonly=True)

    @api.onchange('project_id')
    def _onchange_project_id_propagate_analytic(self):
        if self.project_id and self.project_id.analytic_account_id:
            # Propagate analytic account to all lines
            distribution = {str(self.project_id.analytic_account_id.id): 100.0}
            for line in self.invoice_line_ids:
                line.analytic_distribution = distribution

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    construction_phase_id = fields.Many2one('construction.phase', string='Construction Phase', domain="[('lifecycle_id', '=', lifecycle_id)]")
    lifecycle_id = fields.Many2one('construction.lifecycle', related='move_id.lifecycle_id')
    cost_line_id = fields.Many2one('construction.cost.sheet.line', string='Legacy BOQ Line')
    cost_line_id_ref = fields.Reference(selection=[
        ('construction.cost.material.line', 'Material Line'),
        ('construction.cost.labor.line', 'Labor Line'),
        ('construction.cost.equipment.line', 'Equipment Line'),
        ('construction.cost.vehicle.line', 'Vehicle Line'),
        ('construction.cost.overhead.line', 'Overhead Line')
    ], string='Specialized Budget Line', help="Link this invoice line to a specific specialized budget allocation")

    @api.onchange('product_id')
    def _onchange_product_id_propagate_project_analytic(self):
        if self.move_id.project_id and self.move_id.project_id.analytic_account_id:
            self.analytic_distribution = {str(self.move_id.project_id.analytic_account_id.id): 100.0}
        
        # Suggest valid specialized BOQ line for vendor bills
        if self.move_id.move_type == 'in_invoice' and self.product_id and self.move_id.project_id:
            # Check Material Budget first
            mat_domain = [
                ('product_id', '=', self.product_id.id),
                ('cost_sheet_id.project_id', '=', self.move_id.project_id.id)
            ]
            if self.construction_phase_id:
                mat_domain.append(('phase_id', '=', self.construction_phase_id.id))
            
            match = self.env['construction.cost.material.line'].search(mat_domain, limit=1)
            if match:
                self.cost_line_id_ref = f'construction.cost.material.line,{match.id}'
                return

            # Check Equipment Budget
            eq_match = self.env['construction.cost.equipment.line'].search(mat_domain, limit=1)
            if eq_match:
                self.cost_line_id_ref = f'construction.cost.equipment.line,{eq_match.id}'
                return

            # Check Vehicle Budget
            vh_match = self.env['construction.cost.vehicle.line'].search([
                ('vehicle_id', '=', self.product_id.id),
                ('cost_sheet_id.project_id', '=', self.move_id.project_id.id)
            ], limit=1)
            if vh_match:
                self.cost_line_id_ref = f'construction.cost.vehicle.line,{vh_match.id}'
                return

    @api.model
    def cron_check_installments(self):
        import logging
        import requests
        from requests.auth import HTTPBasicAuth
        _logger = logging.getLogger(__name__)

        """ Scans and notifies clients about overdue installments with throttling. """
        today = fields.Date.context_today(self)
        params = self.env['ir.config_parameter'].sudo()
        
        # Configuration Fetching
        base_url = params.get_param('web.base.url')
        twilio_sid = params.get_param('construction_erp.twilio_account_sid')
        twilio_token = params.get_param('construction_erp.twilio_auth_token')
        twilio_from = params.get_param('construction_erp.twilio_from_number')
        tg_token = params.get_param('construction_erp.telegram_bot_token')
        
        interval = int(params.get_param('construction_erp.reminder_interval_days', default=7))
        max_limit = int(params.get_param('construction_erp.max_reminder_limit', default=3))

        # Search Criteria: Post & Unpaid & (No reminder yet OR Reminder interval passed) & Below Max Limit
        overdue_invoices = self.search([
            ('installment_line_id', '!=', False),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date_due', '<=', today),
            ('reminder_count', '<', max_limit),
            ('installment_line_id.plan_id.unit_id.project_id.project_type', '=', 'construction'),
            '|',
            ('last_reminder_sent', '=', False),
            ('last_reminder_sent', '<=', today - relativedelta(days=interval))
        ])

        for inv in overdue_invoices:
            token = f"secure_{inv.id}" # Simplified for demonstration, usually a hash
            link = f"{base_url}/my/installment/receipt/{inv.id}/{token}"
            msg = f"Reminder: Your installment of {inv.amount_residual} {inv.currency_id.name} for {inv.installment_line_id.plan_id.unit_id.name} is overdue. Secure Upload Link: {link}"
            
            notified = False
            error_msgs = []

            # 1. WhatsApp (Twilio) Notification
            if twilio_sid and twilio_token and twilio_from and inv.partner_id.phone:
                try:
                    # Twilio requires To/From prepended with 'whatsapp:'
                    to_number = f"whatsapp:{inv.partner_id.phone}"
                    from_number = twilio_from if twilio_from.startswith('whatsapp:') else f"whatsapp:{twilio_from}"
                    
                    response = requests.post(
                        f"https://api.twilio.org/2010-04-01/Accounts/{twilio_sid}/Messages.json",
                        auth=HTTPBasicAuth(twilio_sid, twilio_token),
                        data={'To': to_number, 'From': from_number, 'Body': msg},
                        timeout=10
                    )
                    if response.status_code in [200, 201]:
                        notified = True
                    else:
                        error_msgs.append(f"Twilio API Error: {response.text}")
                except Exception as e:
                    error_msgs.append(f"WhatsApp Request Failed: {str(e)}")

            # 2. Telegram Notification
            if tg_token and inv.partner_id.telegram_chat_id:
                tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
                try:
                    response = requests.post(
                        tg_url, 
                        json={'chat_id': inv.partner_id.telegram_chat_id, 'text': msg},
                        timeout=10
                    )
                    if response.status_code == 200:
                        notified = True
                    else:
                        error_msgs.append(f"Telegram API Error: {response.text}")
                except Exception as e:
                    error_msgs.append(f"Telegram Request Failed: {str(e)}")

            # Post to Chatter & Update Tracking
            if notified:
                inv.message_post(body=f"<b>Installment Reminder Sent</b> via { 'WhatsApp/Telegram' if notified else 'None' }.")
                inv.write({
                    'last_reminder_sent': today,
                    'reminder_count': inv.reminder_count + 1
                })
            elif error_msgs:
                inv.message_post(body=f"<span style='color:red;'><b>Reminder Failed:</b></span><br/>" + "<br/>".join(error_msgs))

    def action_post(self):
        for move in self:
            # 1. Direct Inspection Check
            if move.inspection_id and move.inspection_id.state != 'passed':
                raise ValidationError(_("You cannot post this bill because the linked inspection has not 'Passed'."))
            
            # 2. Job Order Milestone Check
            if move.move_type == 'in_invoice':
                milestones = self.env['construction.job.milestone'].search([('invoice_id', '=', move.id)])
                for ms in milestones:
                    inspection = self.env['construction.inspection'].search([('milestone_id', '=', ms.id)], limit=1)
                    if inspection and inspection.state != 'passed':
                         raise ValidationError(_("Vendor Bill cannot be posted: Milestone '%s' inspection state is '%s'.") % (ms.name, inspection.state))
                    if not inspection and ms.state == 'pending':
                         raise ValidationError(_("Vendor Bill cannot be posted: Milestone '%s' has no associated inspection records.") % ms.name)
                         
        return super(AccountMove, self).action_post()

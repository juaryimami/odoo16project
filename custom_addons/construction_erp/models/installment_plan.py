# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class InstallmentPlan(models.Model):
    _name = 'real_estate.installment.plan'
    _description = 'Real Estate Installment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']

    name = fields.Char(string='Plan Reference', required=True, states={'active': [('readonly', True)], 'completed': [('readonly', True)]})
    client_id = fields.Many2one('res.partner', string='Client', required=True, domain="[('is_client', '=', True)]", states={'active': [('readonly', True)], 'completed': [('readonly', True)]})
    sale_id = fields.Many2one('sale.order', string='Sale Order', domain="[('partner_id', '=', client_id)]", required=True, states={'active': [('readonly', True)], 'completed': [('readonly', True)]})
    unit_id = fields.Many2one('real_estate.unit', string='Property Unit Type', required=True, states={'active': [('readonly', True)], 'completed': [('readonly', True)]})
    total_amount = fields.Monetary(string='Total Sale Value', related='sale_id.amount_total', store=True, currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='sale_id.currency_id')
    
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id', required=True, states={'active': [('readonly', True)], 'completed': [('readonly', True)]})
    monthly_payment_amount = fields.Monetary(string='Monthly Payment Amount', currency_field='currency_id', required=True, default=0.0, states={'active': [('readonly', True)], 'completed': [('readonly', True)]})
    number_of_months = fields.Integer(string='Payment Duration (Months)', compute='_compute_number_of_months', store=True, tracking=True)
    start_date = fields.Date(string='First Installment Date', required=True, default=fields.Date.context_today, states={'active': [('readonly', True)], 'completed': [('readonly', True)]})

    @api.depends('total_amount', 'deposit_amount', 'monthly_payment_amount')
    def _compute_number_of_months(self):
        for plan in self:
            remaining = plan.total_amount - plan.deposit_amount
            if plan.monthly_payment_amount > 0:
                num_full_months = int(remaining // plan.monthly_payment_amount)
                remainder = remaining - (num_full_months * plan.monthly_payment_amount)
                plan.number_of_months = num_full_months + (1 if remainder > 0.001 else 0)
            else:
                plan.number_of_months = 0

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed')
    ], string='Status', default='draft', tracking=True)
    
    @api.model
    def cron_auto_generate_invoices(self):
        """ Scans installment lines approaching their due date and issues invoices. """
        params = self.env['ir.config_parameter'].sudo()
        days_ahead = int(params.get_param('construction_erp.auto_invoice_days', default=7))
        target_date = fields.Date.context_today(self) + relativedelta(days=days_ahead)
        
        lines = self.env['real_estate.installment.line'].search([
            ('is_invoiced', '=', False),
            ('due_date', '<=', target_date),
            ('plan_id.state', '=', 'active'),
            ('plan_id.unit_id.project_id.project_type', '=', 'construction')
        ])
        for line in lines:
            line.action_create_invoice()

    line_ids = fields.One2many('real_estate.installment.line', 'plan_id', string='Installments')

    def action_generate_schedule(self):
        for plan in self:
            plan.line_ids.unlink() # Clear existing
            
            # Step 1: Create Deposit
            self.env['real_estate.installment.line'].create({
                'plan_id': plan.id,
                'name': 'Initial Deposit',
                'amount': plan.deposit_amount,
                'due_date': fields.Date.context_today(self),
            })
            
            # Step 2: Calculate remaining
            remaining = plan.total_amount - plan.deposit_amount
            
            if plan.monthly_payment_amount > 0:
                num_full_months = int(remaining // plan.monthly_payment_amount)
                remainder = remaining - (num_full_months * plan.monthly_payment_amount)
                total_months = num_full_months + (1 if remainder > 0.001 else 0)
                
                for i in range(1, total_months + 1):
                    due_date = plan.start_date + relativedelta(months=i-1)
                    if i == total_months and remainder > 0.001:
                        amount = remainder
                    else:
                        amount = plan.monthly_payment_amount
                        
                    self.env['real_estate.installment.line'].create({
                        'plan_id': plan.id,
                        'name': f'Installment {i} of {total_months}',
                        'amount': amount,
                        'due_date': due_date,
                    })
            plan.state = 'active'

    def action_open_invoice_wizard(self):
        self.ensure_one()
        return {
            'name': _('Quick Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'installment.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_plan_id': self.id},
        }

    def _notify_installment_invoice(self, move, lines):
        """ Reusable notification logic for installment invoices. """
        self.ensure_one()
        partner = self.client_id
        pref = partner.notification_preference or 'email'
        
        # 1. SECURITY TOKEN
        if not move.payment_token:
            import uuid
            move.sudo().write({'payment_token': str(uuid.uuid4())})

        # 2. EMAIL BLOCK
        try:
            template = self.env.ref('construction_erp.email_template_real_estate_installment', raise_if_not_found=False)
            if not template:
                template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
                
            if template:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                payment_url = "%s/payment/receipt/%s?access_token=%s" % (base_url, move.id, move.payment_token)

                # pyrefly: ignore [missing-import]
                from odoo.tools import format_amount
                ctx = {
                    'payment_url': payment_url,
                    'invoice_name': move.name,
                    'invoice_origin': move.invoice_origin or 'N/A',
                    'unit_name': self.unit_id.name or 'N/A',
                    'line_name': lines[0].name if lines else 'Multiple Installments',
                    'amount_formatted': format_amount(self.env, move.amount_total, move.currency_id),
                    'due_date': lines[0].due_date if lines else move.invoice_date_due,
                }
                template.with_context(**ctx).send_mail(partner.id, force_send=True)
                
                # Explicitly log to Invoice and Sales Order
                mail_log = _("<b>Email Sent:</b> Payment reminder delivered to %s") % partner.email
                move.sudo().message_post(body=mail_log, message_type='comment', subtype_xmlid='mail.mt_comment')
                if self.sale_id:
                    self.sale_id.sudo().message_post(body=mail_log, message_type='comment', subtype_xmlid='mail.mt_comment')
        except Exception as email_e:
            _logger.error("Failed to send email reminder: %s", str(email_e))

        # 3. MOBILE BLOCK (Delegated to Mixin for Preference Handling)
        try:
            import html
            # Force HTTPS and use the specific domain for the relative path
            base_url = "https://internal.nemalrealestate.com"
            payment_path = "payment/receipt/%s?access_token=%s" % (move.id, move.payment_token)
            payment_url = "%s/%s" % (base_url, payment_path)
            
            amount_str = format_amount(self.env, move.amount_total, move.currency_id).replace('\xa0', ' ')
            # Fetch Unit Name (e.g., Apartment 101) instead of Project Name
            unit_name = self.sale_id.unit_id.name or "Property"
            
            mobile_msg = (
                "🏢 *NEMAL ENGINEERING - REAL ESTATE*\n\n"
                "Dear *%s*,\n\n"
                "This is a formal reminder regarding your installment payment for:\n"
                "📍 %s\n\n"
                "💰 Property Purchased: %s\n"
                "💰 Total Amount Due: %s\n"
                "📅 Invoice Date: %s\n"
                "📄 Invoice Ref: %s\n\n"
                "Please complete your payment using the secure link below:\n"
                "%s\n\n"
                "After payment, kindly upload your bank receipt through the provided payment page.\n\n"
                "Thank you for choosing Nemal Engineering."
            ) % (
                partner.name, 
                self.sale_id.name or self.name,
                unit_name,
                amount_str,
                move.invoice_date, move.name,
                payment_url
            )

            markup = {
                'inline_keyboard': [[
                    {'text': '📤 Upload Bank Receipt', 'url': payment_url}
                ]]
            }

            # Check if a Template SID is configured to bypass 24h window
            template_sid = self.env['ir.config_parameter'].sudo().get_param('construction_erp.whatsapp_installment_template_sid')
            template_vars = None
            if template_sid:
                template_vars = {
                    "1": partner.name,
                    "2": self.sale_id.name or self.name,
                    "3": unit_name,
                    "4": amount_str,
                    "5": str(move.invoice_date),
                    "6": move.name,
                    "7": payment_path
                }

            # High-level call handles preference automatically
            _logger.info("Attempting to notify contact %s for invoice %s (Template: %s)", partner.name, move.name, template_sid or 'None')
            sent = self.notify_contact(partner, mobile_msg, reply_markup=markup, template_sid=template_sid, template_variables=template_vars)
            
            if sent:
                _logger.info("Notification sent successfully, posting to chatter...")
                # 4. CROSS-MODEL LOGGING
                # Include the actual message content for audit
                log_body = _("<b>Mobile Notification Sent</b> via Telegram/WhatsApp:<br/><pre>%s</pre>") % mobile_msg
                
                # Log to Invoice
                move.sudo().message_post(
                    body=log_body,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
                
                # Log to Sales Order
                if self.sale_id:
                    self.sale_id.sudo().message_post(
                        body=log_body,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment'
                    )
            else:
                _logger.warning("Notification failed to send for invoice %s", move.name)
            
        except Exception as mobile_e:
            _logger.error("CRITICAL: Failed in notification loop: %s", str(mobile_e))


class InstallmentLine(models.Model):
    _name = 'real_estate.installment.line'
    _description = 'Installment Schedule Line'

    plan_id = fields.Many2one('real_estate.installment.plan', string='Plan')
    name = fields.Char(string='Description', required=True)
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='plan_id.currency_id')
    due_date = fields.Date(string='Due Date', required=True)
    
    invoice_id = fields.Many2one('account.move', string='Generated Invoice')
    is_invoiced = fields.Boolean(string='Invoiced', compute='_compute_is_invoiced', store=True)
    invoice_payment_state = fields.Selection(related='invoice_id.payment_state', string='Payment Status')

    @api.depends('invoice_id', 'invoice_id.state', 'invoice_id.payment_state')
    def _compute_is_invoiced(self):
        for line in self:
            line.is_invoiced = bool(line.invoice_id)

    def action_create_invoice(self):
        for line in self:
            if not line.invoice_id:
                # Check for analytic account
                analytic_id = line.plan_id.unit_id.project_id.analytic_account_id.id if line.plan_id.unit_id.project_id.analytic_account_id else False
                
                try:
                    # Find the first sale order line to link the invoice line (for smart button visibility)
                    sale_line = line.plan_id.sale_id.order_line[0] if line.plan_id.sale_id and line.plan_id.sale_id.order_line else False
                    
                    vals = {
                        'move_type': 'out_invoice',
                        'partner_id': line.plan_id.client_id.id,
                        'project_id': line.plan_id.unit_id.project_id.id if line.plan_id.unit_id.project_id else False,
                        'invoice_origin': line.plan_id.sale_id.name if line.plan_id.sale_id else line.plan_id.name,
                        'installment_line_ids': [(6, 0, [line.id])],
                        'invoice_date': fields.Date.context_today(self),
                        'invoice_date_due': line.due_date,
                        'invoice_line_ids': [(0, 0, {
                            'name': line.name,
                            'quantity': 1,
                            'price_unit': line.amount,
                            'product_id': self.env.ref('construction_erp.product_installment_payment').id,
                            'analytic_distribution': {str(analytic_id): 100} if analytic_id else False,
                            'sale_line_ids': [(6, 0, [sale_line.id])] if sale_line else False,
                            'tax_ids': [(6, 0, sale_line.tax_id.ids)] if sale_line and sale_line.tax_id else [(5, 0, 0)],
                        })]
                    }
                    move = self.env['account.move'].create(vals)
                    line.invoice_id = move.id
                    
                    # Post to Sales Order Chatter about creation
                    if line.plan_id.sale_id:
                        line.plan_id.sale_id.message_post(
                            body=_("<b>Automated Billing:</b> Invoice created for installment: <i>%s</i>") % line.name
                        )

                    try:
                        move.action_post()
                        # Call the unified notification method
                        line.plan_id._notify_installment_invoice(move, line)
                    except Exception as post_e:
                        _logger.error("Failed to post/notify invoice: %s", str(post_e))
                except Exception as e:
                    _logger.error("Failed to create invoice for installment line %s: %s", line.id, str(e))
                    if line.plan_id.sale_id:
                        line.plan_id.sale_id.message_post(body=_("<b>Error:</b> Failed to create invoice for installment %s: %s") % (line.name, str(e)))
    def action_resend_notification(self):
        self.ensure_one()
        if self.invoice_id and self.invoice_id.state == 'posted':
            self.plan_id._notify_installment_invoice(self.invoice_id, self)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Notification Resent'),
                    'message': _('The notification has been sent to %s.') % self.plan_id.client_id.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_("You can only resend notifications for posted invoices."))

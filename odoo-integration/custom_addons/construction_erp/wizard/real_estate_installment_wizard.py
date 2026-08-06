from odoo import models, fields, api, _
import base64
import logging
_logger = logging.getLogger(__name__)

class RealEstateInstallmentWizard(models.TransientModel):
    _name = 'real.estate.installment.wizard'
    _description = 'Real Estate Installment Configuration Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', required=True)
    deposit_amount = fields.Monetary(string='Initial Deposit', required=True)
    currency_id = fields.Many2one('res.currency', related='sale_order_id.currency_id')
    
    monthly_payment_amount = fields.Monetary(string='Monthly Payment Amount', required=True, default=0.0)
    start_date = fields.Date(string='First Installment Date', required=True, default=fields.Date.context_today)
    
    agreement_file = fields.Binary(string='Sales Agreement Document', required=True)
    agreement_filename = fields.Char(string='Agreement Filename')

    def action_confirm_installment(self):
        self.ensure_one()
        sale = self.sale_order_id
        _logger.info("Confirming installment for Sale Order %s", sale.name)
        
        # 1. Create the Installment Plan first
        plan = self.env['real_estate.installment.plan'].create({
            'name': _('Plan for %s') % sale.name,
            'client_id': sale.partner_id.id,
            'sale_id': sale.id,
            'unit_id': sale.unit_id.id,
            'deposit_amount': self.deposit_amount,
            'monthly_payment_amount': self.monthly_payment_amount,
            'start_date': self.start_date,
        })
        _logger.info("Installment Plan created: %s", plan.id)
        
        # 2. Confirm the Sale Order (Explicitly bypass wizard trigger)
        sale.with_context(skip_installment_wizard=True).action_confirm()
        _logger.info("Sale Order %s confirmed. State: %s", sale.name, sale.state)
        
        # 3. Attach the Sales Agreement to the Sale Order
        if self.agreement_file:
            attachment = self.env['ir.attachment'].create({
                'name': self.agreement_filename or 'Sales_Agreement.pdf',
                'type': 'binary',
                'datas': self.agreement_file,
                'res_model': 'sale.order',
                'res_id': sale.id,
            })
            sale.message_post(
                body=_("<b>Sales Agreement Document</b> has been attached and confirmed."),
                attachment_ids=[attachment.id]
            )
        
        # 4. Generate the Schedule
        plan.action_generate_schedule()
        _logger.info("Schedule generated for plan %s. Lines: %s", plan.id, len(plan.line_ids))
        
        # 5. Create Initial Deposit Invoice
        # We search for the first line with a positive amount (Deposit)
        deposit_line = self.env['real_estate.installment.line'].search([
            ('plan_id', '=', plan.id),
            ('amount', '>', 0)
        ], order='due_date asc', limit=1)
        
        if deposit_line:
            _logger.info("Found deposit line %s for sale %s, creating invoice...", deposit_line.id, sale.name)
            try:
                deposit_line.action_create_invoice()
                sale.message_post(body="<b>Real Estate Workflow:</b> Initial Deposit Invoice created automatically.")
            except Exception as e:
                _logger.error("Failed to create deposit invoice: %s", str(e))
                sale.message_post(body="<b>Error:</b> Automatic Deposit Invoicing failed: %s" % str(e))
        else:
            _logger.warning("COULD NOT FIND DEPOSIT LINE FOR PLAN %s", plan.id)
            sale.message_post(body="<b>Warning:</b> No deposit line found to invoice automatically.")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'real_estate.installment.plan',
            'res_id': plan.id,
            'view_mode': 'form',
            'target': 'current',
        }

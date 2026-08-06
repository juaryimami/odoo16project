# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class InstallmentInvoiceWizard(models.TransientModel):
    _name = 'installment.invoice.wizard'
    _description = 'Installment Invoice Wizard'

    plan_id = fields.Many2one('real_estate.installment.plan', string='Installment Plan', required=True)
    client_id = fields.Many2one('res.partner', related='plan_id.client_id')
    currency_id = fields.Many2one('res.currency', related='plan_id.currency_id')
    
    method = fields.Selection([
        ('selection', 'Select Specific Installments'),
        ('amount', 'Enter Total Amount to Pay')
    ], string='Invoicing Method', default='selection', required=True)
    
    line_ids = fields.Many2many('real_estate.installment.line', string='Installments', 
                                domain="[('plan_id', '=', plan_id), ('is_invoiced', '=', False)]")
    
    total_amount = fields.Monetary(string='Amount to Invoice', currency_field='currency_id')
    invoice_date = fields.Date(string='Invoice Date', default=fields.Date.context_today, required=True)
    invoice_date_due = fields.Date(string='Due Date', help="Payment deadline for this invoice")

    @api.onchange('line_ids', 'method')
    def _onchange_lines(self):
        if self.method == 'selection':
            self.total_amount = sum(self.line_ids.mapped('amount'))
            if self.line_ids:
                # Set due date to the earliest selected line's due date
                self.invoice_date_due = min(self.line_ids.mapped('due_date'))

    def action_create_invoice(self):
        self.ensure_one()
        if self.method == 'selection' and not self.line_ids:
            raise UserError(_("Please select at least one installment line."))
        if self.method == 'amount' and self.total_amount <= 0:
            raise UserError(_("Please enter a valid amount to invoice."))

        target_lines = self.env['real_estate.installment.line']
        if self.method == 'selection':
            target_lines = self.line_ids
            amount_to_invoice = sum(target_lines.mapped('amount'))
            description = _("Installment Payment(s): %s") % ", ".join(target_lines.mapped('name'))
        else:
            amount_to_invoice = self.total_amount
            description = _("Partial Installment Payment - %s") % self.plan_id.name
            
            # Amount Mode: Find upcoming un-invoiced lines
            all_lines = self.env['real_estate.installment.line'].search([
                ('plan_id', '=', self.plan_id.id),
                ('is_invoiced', '=', False)
            ], order='due_date asc')
            
            remaining_val = self.total_amount
            for line in all_lines:
                if remaining_val <= 0:
                    break
                
                if remaining_val >= line.amount:
                    # Fully cover this line
                    target_lines |= line
                    remaining_val -= line.amount
                else:
                    # Partially cover this line
                    # Split the line: create a new line for the covered amount
                    new_line = self.env['real_estate.installment.line'].create({
                        'plan_id': line.plan_id.id,
                        'name': f"{line.name} (Partial)",
                        'amount': remaining_val,
                        'due_date': line.due_date,
                    })
                    target_lines |= new_line
                    
                    # Deduct from line amount and stop
                    line.amount -= remaining_val
                    remaining_val = 0

        # Create Invoice
        project = self.plan_id.unit_id.project_id
        analytic_account = project.analytic_account_id if project else False
        analytic_id = analytic_account.id if analytic_account else False
        sale_line = self.plan_id.sale_id.order_line[0] if self.plan_id.sale_id and self.plan_id.sale_id.order_line else False
        
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.plan_id.client_id.id,
            'invoice_origin': self.plan_id.sale_id.name if self.plan_id.sale_id else self.plan_id.name,
            'project_id': project.id if project else False,
            'invoice_date': self.invoice_date,
            'invoice_date_due': self.invoice_date_due or self.invoice_date,
            'installment_line_ids': [(6, 0, target_lines.ids)],
            'invoice_line_ids': [(0, 0, {
                'name': description,
                'quantity': 1,
                'price_unit': amount_to_invoice,
                'product_id': self.env.ref('construction_erp.product_installment_payment').id,
                'analytic_distribution': {str(analytic_id): 100} if analytic_id else False,
                'sale_line_ids': [(6, 0, [sale_line.id])] if sale_line else False,
                'tax_ids': [(6, 0, sale_line.tax_id.ids)] if sale_line and sale_line.tax_id else [(5, 0, 0)],
            })]
        }
        
        # Use sudo for creation and posting to bypass permission/constraint issues
        move = self.env['account.move'].sudo().create(invoice_vals)
        
        # Link lines to invoice (CRITICAL: This marks them as Invoiced)
        for line in target_lines:
            line.sudo().write({'invoice_id': move.id})
        
        # Post and Notify
        try:
            with self.env.cr.savepoint():
                move.sudo().action_post()
        except Exception as e:
            _logger.error("Failed to auto-post invoice: %s. Invoice remains in Draft.", str(e))
            # If posting fails due to analytics, we leave it in Draft so the user can fix it
            pass
        
        # Chatter Log on Sales Order (Now safe because of savepoint)
        if self.plan_id.sale_id:
            self.plan_id.sale_id.sudo().message_post(
                body=_("<b>Manual Billing:</b> Custom invoice created for <b>%s %s</b>") % (amount_to_invoice, self.currency_id.name),
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

        # Trigger the premium notification flow (Will use Draft invoice if posting failed)
        self.plan_id._notify_installment_invoice(move, target_lines)
        
        return {
            'name': _('Generated Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': move.id,
            'type': 'ir.actions.act_window',
        }

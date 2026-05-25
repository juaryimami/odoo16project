from odoo import models, fields, api

from num2words import  num2words

# Extending the Purchase Order model
class CustomSalesInvoice(models.Model):
    _inherit = 'account.move'
    amount_in_word=fields.Char("Amount in word",compute="compute_service_and_amount" )
    service=fields.Char(string="Service",compute="compute_service_and_amount")
    location=fields.Char(string="Service",compute="compute_service_and_amount")
    formatted_invoice_date = fields.Char(string="Formatted Invoice Date", compute="_compute_formatted_invoice_date",
                                         store=False)

    def _compute_formatted_invoice_date(self):
        for order in self:
            if order.invoice_date:
                order.formatted_invoice_date = order.invoice_date.strftime("%B, %Y")  # e.g., "July, 2024"
            else:
                order.formatted_invoice_date = "N/A"  # Handle None case


    def compute_service_and_amount(self):
        for rec in self:
            rec.amount_in_word=num2words(rec.amount_total)
            sales=self.env['sale.order'].search(
                [('name', '=', rec.invoice_origin)], limit=1)
            if len(sales)>0:
                rec.service=sales.operation_id.contract_name
                rec.location=sales.location_id.name
            else:
                rec.service = ""
                rec.location = ""

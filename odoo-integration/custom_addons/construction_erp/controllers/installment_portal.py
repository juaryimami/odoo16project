# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import base64

class InstallmentPortal(http.Controller):

    @http.route(['/my/installment/receipt/<int:invoice_id>/<string:token>'], type='http', auth="public", website=True)
    def upload_receipt_form(self, invoice_id, token, **kwargs):
        # Security Check (Simplified token matching for this prototype)
        invoice = request.env['account.move'].sudo().browse(invoice_id)
        if not invoice.exists() or token != f"secure_{invoice.id}":
            return request.render('http_routing.404')
        
        if request.httprequest.method == 'POST' and kwargs.get('receipt_file'):
            file_data = kwargs.get('receipt_file').read()
            filename = kwargs.get('receipt_file').filename
            
            # Create attachment
            attachment = request.env['ir.attachment'].sudo().create({
                'name': filename,
                'datas': base64.b64encode(file_data),
                'res_model': 'account.move',
                'res_id': invoice.id,
            })
            
            # Post to chatter
            invoice.message_post(
                body=_("<b>Payment Receipt Uploaded</b> by client via secure link."),
                attachment_ids=[attachment.id]
            )
            
            # Create an activity for the accountant
            accountant_group = request.env.ref('account.group_account_invoice')
            accountants = request.env['res.users'].sudo().search([('groups_id', 'in', [accountant_group.id])], limit=1)
            if accountants:
                invoice.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_("Verify Payment Receipt"),
                    note=_("A new receipt has been uploaded for this installment. Please verify and register payment."),
                    user_id=accountants[0].id
                )

            return request.render('construction_erp.receipt_upload_success', {
                'invoice': invoice
            })

        return request.render('construction_erp.receipt_upload_portal', {
            'invoice': invoice,
            'token': token
        })

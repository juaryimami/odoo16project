from odoo import http, _, fields
from odoo.http import request
import binascii

class PaymentReceiptPortal(http.Controller):

    @http.route(['/payment/receipt/<int:invoice_id>'], type='http', auth="public", website=True, sitemap=False, csrf=False)
    def portal_payment_receipt(self, invoice_id, access_token=None, **kw):
        # Basic security: We check the invoice exists and is valid
        invoice = request.env['account.move'].sudo().browse(invoice_id)
        if not invoice.exists() or invoice.move_type != 'out_invoice':
            return request.render('website.404')

        # Verify Security Token
        if not access_token or access_token != invoice.payment_token:
            return request.render('website.404')

        values = {
            'invoice': invoice,
            'has_receipt': invoice.payment_receipt_uploaded,
            'company': invoice.company_id,
        }
        return request.render('construction_erp.portal_payment_receipt_upload', values)

    @http.route(['/payment/receipt/submit'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def payment_receipt_submit(self, **kw):
        invoice_id = kw.get('invoice_id')
        access_token = kw.get('access_token')
        receipt_file = kw.get('receipt_file')
        
        invoice = request.env['account.move'].sudo().browse(int(invoice_id))
        if not invoice.exists() or invoice.payment_token != access_token:
            return request.render('website.404')
        
        if not receipt_file:
            return request.redirect('/payment/receipt/%s' % invoice_id)

        # 1. Attach the file to the Invoice
        file_data = receipt_file.read()
        attachment = request.env['ir.attachment'].sudo().create({
            'name': 'Payment_Receipt_%s_%s' % (invoice.name.replace('/', '_'), receipt_file.filename),
            'type': 'binary',
            'datas': binascii.b2a_base64(file_data),
            'res_model': 'account.move',
            'res_id': invoice.id,
        })

        # 2. Post to Invoice Chatter
        invoice.sudo().message_post(
            body=_("<b>Payment Proof Received:</b> A new payment receipt has been uploaded via the customer portal."),
            attachment_ids=[attachment.id],
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )

        # 3. Mark as uploaded (to expire the link)
        invoice.sudo().write({'payment_receipt_uploaded': True})

        # 4. Notify Sales Order and Plan
        sale = False
        plan = False
        
        # Check both old (Many2one) and new (Many2many) fields
        if invoice.installment_line_id:
            plan = invoice.installment_line_id.plan_id
        elif invoice.installment_line_ids:
            plan = invoice.installment_line_ids[0].plan_id
            
        if plan:
            sale = plan.sale_id
            # Log to Plan
            plan.sudo().message_post(
                body=_("<b>Portal Update:</b> Receipt uploaded for invoice <b>%s</b>.") % invoice.name,
                attachment_ids=[attachment.id],
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

        if sale:
            # Log to Sales Order
            sale.sudo().message_post(
                body=_("<b>Portal Update:</b> Customer uploaded payment proof for invoice <b>%s</b>.") % invoice.name,
                attachment_ids=[attachment.id],
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

        return request.render('construction_erp.portal_payment_receipt_success', {'invoice': invoice})

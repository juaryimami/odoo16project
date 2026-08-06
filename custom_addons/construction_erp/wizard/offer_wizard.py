# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import base64

class JobOrderOfferWizard(models.TransientModel):
    _name = 'construction.job.offer.wizard'
    _description = 'Job Order Offer Wizard'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order', required=True)
    partner_id = fields.Many2one('res.partner', string='Contractor', related='job_order_id.contractor_id')
    contract_type = fields.Selection(related='job_order_id.contract_type', string='Agreement Type')
    email_template_id = fields.Many2one('mail.template', string='Email Template')
    subject = fields.Char(string='Subject', required=True)
    body = fields.Html(string='Email Content', required=True)
    pm_name = fields.Char(string='Project Manager Name', required=True, default=lambda self: self.env.user.name)
    pm_signature = fields.Binary(string='Your Signature', required=True)
    advance_payment_pct = fields.Float(string='Advance Payment %')
    attachment_ids = fields.Many2many('ir.attachment', string='Extra Attachments')

    # REMOVED onchange that was resetting subject to raw template

    def action_send_offer(self):
        self.ensure_one()
        order = self.job_order_id
        
        # 0. Persist PM Signature and Advance Payment Pct to Job Order
        order.write({
            'pm_name': self.pm_name,
            'pm_signature': self.pm_signature,
            'advance_payment_pct': self.advance_payment_pct,
        })
        
        # 1. Generate the PDF Report
        report_xml_id = 'construction_erp.action_report_job_order_contract'
        pdf_content, content_type = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report_xml_id, [order.id])
        
        pdf_attachment = self.env['ir.attachment'].create({
            'name': f'Job_Order_{order.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'construction.job.order',
            'res_id': order.id,
            'mimetype': 'application/pdf',
        })

        # 2. Collect all attachments (Auto PDF + Wizard manual attachments)
        all_attachment_ids = [pdf_attachment.id] + self.attachment_ids.ids

        # 3. Send the Email & Log in Chatter
        # We use message_post to handle both sending and logging in a professional Odoo way
        order.with_context(mail_post_autofollow=True).message_post(
            subject=self.subject,
            body=self.body,
            partner_ids=[order.contractor_id.id],
            attachment_ids=all_attachment_ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        # 4. Update Job Order State
        order.write({'state': 'offered'})
        
        return {'type': 'ir.actions.act_window_close'}

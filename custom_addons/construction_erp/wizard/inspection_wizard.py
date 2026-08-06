# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class QualityInspectionWizard(models.TransientModel):
    _name = 'construction.inspection.wizard'
    _description = 'Quality Inspection Gate Wizard'

    job_order_id = fields.Many2one('construction.job.order', string='Job Order', required=True)
    inspection_id = fields.Many2one('construction.inspection', string='Inspection Reference', required=True)
    inspector_id = fields.Many2one('res.partner', string='Assigned Inspector', related='inspection_id.inspector_id')
    phase_id = fields.Many2one('construction.phase', string='Construction Phase')
    
    subject = fields.Char(string='Email Subject', required=True)
    body = fields.Html(string='Email Content', required=True)

    def action_send_request(self):
        self.ensure_one()
        inspection = self.inspection_id
        job = self.job_order_id
        
        # 1. Send the email and log in chatter
        # We partner_ids to the inspector to ensure they receive it
        job.with_context(mail_post_autofollow=True).message_post(
            subject=self.subject,
            body=self.body,
            partner_ids=[inspection.inspector_id.id],
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        
        # Also log in the inspection record itself for audit consistency
        inspection.message_post(
            body=_("Formal Inspection Request sent to %s via Portal Gate.") % inspection.inspector_id.name,
            message_type='notification'
        )

        # 2. Update Job Order State to 'ready_for_inspection'
        # Note: We do this ONLY when the email is sent
        job.write({
            'state': 'ready_for_inspection',
            'date_finish_actual': fields.Datetime.now()
        })
        
        return {'type': 'ir.actions.act_window_close'}

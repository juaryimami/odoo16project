# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
import random
import string

class ConstructionPortalAccessWizard(models.TransientModel):
    _name = 'construction.portal.access.wizard'
    _description = 'Generate Portal Access'

    sale_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    partner_id = fields.Many2one('res.partner', related='sale_id.partner_id', string='Customer')
    email = fields.Char(related='partner_id.email', readonly=False, required=True)
    username = fields.Char(string='Username', required=True)
    password = fields.Char(string='Generated Password', required=True)
    portal_link = fields.Char(string='Portal Link', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(ConstructionPortalAccessWizard, self).default_get(fields_list)
        if self.env.context.get('active_id'):
            sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
            res['sale_id'] = sale.id
            res['password'] = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            # Suggest username as email if exists, else first name + id
            if sale.partner_id.email:
                res['username'] = sale.partner_id.email
            else:
                safe_name = "".join(c for c in sale.partner_id.name if c.isalnum()).lower()
                res['username'] = f"{safe_name}{sale.partner_id.id}"

            base_url = "https://internal.nemalrealestate.com"
            res['portal_link'] = f"{base_url}/portal_app"
        return res

    def action_grant_access(self):
        self.ensure_one()
        if not self.partner_id.email:
            self.partner_id.email = self.username

        # Check if user exists
        user = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)], limit=1)
        if not user:
            portal_group = self.env.ref('base.group_portal')
            user = self.env['res.users'].create({
                'name': self.partner_id.name,
                'login': self.username,
                'partner_id': self.partner_id.id,
                'groups_id': [(6, 0, [portal_group.id])],
                'email': self.email
            })
        
        # Set password
        user.password = self.password
        
        # Send Email via Chatter to ensure it always displays in the UI
        template = self.env.ref('construction_erp.email_template_portal_access_generated', raise_if_not_found=False)
        if template:
            self.sale_id.with_context(
                portal_username=self.username,
                portal_password=self.password,
                portal_link=self.portal_link,
                force_send=True
            ).message_post_with_template(
                template.id,
                email_layout_xmlid="mail.mail_notification_light",
                composition_mode='comment'
            )

        return {'type': 'ir.actions.act_window_close'}

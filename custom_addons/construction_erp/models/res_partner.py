import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_contractor = fields.Boolean(string='Is Contractor')
    is_client = fields.Boolean(string='Is Client')
    
    # Client Registration Fields
    file_number = fields.Char(string='File Number')
    site_name = fields.Char(string='Site Name')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string='Gender')
    mother_name = fields.Char(string="Mother's Name")
    nationality = fields.Char(string='Nationality')
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ], string='Marital Status')
    spouse_name = fields.Char(string='Spouse Name')
    
    # Address Fields
    region = fields.Char(string='Region')
    zone = fields.Char(string='Zone')
    woreda = fields.Char(string='Woreda')
    kebele = fields.Char(string='Kebele')
    house_no = fields.Char(string='House No')
    
    id_no = fields.Char(string='ID No')
    project_ids = fields.Many2many('project.project', string='Projects', compute='_compute_project_ids', store=True)
    bought_project_id = fields.Many2one('project.project', string='Bought Project', compute='_compute_bought_project_id', store=True)
    amount_of_share = fields.Integer(string='Amount of Share')

    @api.depends('sale_order_ids', 'sale_order_ids.project_id')
    def _compute_project_ids(self):
        for partner in self:
            # Map all projects from the partner's sale orders
            projects = partner.sale_order_ids.mapped('project_id')
            partner.project_ids = projects

    @api.depends('sale_order_ids', 'sale_order_ids.project_id')
    def _compute_bought_project_id(self):
        for partner in self:
            # Get the first project from their sales orders
            orders = partner.sale_order_ids.filtered(lambda s: s.project_id)
            partner.bought_project_id = orders[0].project_id if orders else False

    receipt_upload_pin = fields.Char(string='Receipt Upload PIN')
    
    notification_preference = fields.Selection([
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp (Twilio)'),
        ('telegram', 'Telegram')
    ], string='Notification Preference', default='email', help="Choose how the customer receives automated installment invoices.")
    
    whatsapp_number = fields.Char(string='WhatsApp Number', help="Enter number in international format, e.g., +123456789")
    telegram_chat_id = fields.Char(string='Telegram Chat ID')

    def action_sync_telegram_id_nemal(self):
        """ Fetch Telegram Chat ID and IMMEDIATELY update the record. """
        self.ensure_one()
        
        # 1. Configuration Check
        token = self.env['ir.config_parameter'].sudo().get_param('construction_erp.telegram_bot_token')
        if not token:
            raise UserError(_("Configuration Error: Please add the Telegram Bot Token in Settings first."))

        # 2. Fetch Data from Telegram
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                raise UserError(_("Telegram API Error: Connection failed. Please check your Bot Token."))

            updates = response.json().get('result', [])
            if not updates:
                raise UserError(_("No recent messages found. \n\n"
                                 "WORKFLOW:\n"
                                 "1. Open the Bot in Telegram.\n"
                                 "2. Click Attachment > Contact > Share Contact.\n"
                                 "3. Then click Sync in Odoo."))

            # 3. Smart Matching Logic
            def normalize(num):
                return ''.join(filter(str.isdigit, str(num or '')))[-9:]

            target_phone = normalize(self.phone)
            target_mobile = normalize(self.mobile)
            target_name = (self.name or '').lower().strip()
            
            found_chat_id = False
            for update in reversed(updates):
                message = update.get('message', {})
                user = message.get('from', {})
                contact = message.get('contact', {})
                
                # Priority 1: Phone Match (Last 9 Digits)
                if contact and contact.get('phone_number'):
                    contact_phone = normalize(contact['phone_number'])
                    if contact_phone and (contact_phone == target_phone or contact_phone == target_mobile):
                        found_chat_id = user.get('id')
                        break
                
                # Priority 2: Name Match
                first_name = (user.get('first_name') or '').lower().strip()
                last_name = (user.get('last_name') or '').lower().strip()
                full_name = f"{first_name} {last_name}".strip()
                
                if target_name and (full_name == target_name or first_name == target_name):
                    found_chat_id = user.get('id')
                    break

            # 4. Apply and Save
            if found_chat_id:
                self.write({'telegram_chat_id': str(found_chat_id)})
                # Force commit so the user sees it even if they don't save the form
                self.env.cr.commit() 
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Telegram Linked!'),
                        'message': _('Successfully found Chat ID %s for %s.') % (found_chat_id, self.name),
                        'sticky': False,
                        'type': 'success',
                        'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    }
                }
            else:
                raise UserError(_("Match Not Found for '%s'. \n\n"
                                 "REQUIRED STEP: In Telegram, you MUST click 'Share Contact' so the bot can see your phone number.") % self.name)

        except Exception as e:
            if isinstance(e, UserError):
                raise e
            _logger.exception("Telegram Sync Workflow Failed")
            raise UserError(_("Technical Error: %s") % str(e))

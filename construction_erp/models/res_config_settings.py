# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Fallback for standard Odoo field to satisfy JS client metadata requirements
    pay_invoices_online = fields.Boolean(
        string='Pay Invoices Online',
        config_parameter='portal.pay_invoices_online'
    )

    construction_auto_generate_rfq = fields.Boolean(
        string='Automated RFQ Generation',
        config_parameter='construction_erp.auto_generate_rfq',
        default=True,
        help="Automatically generate Draft POs when material requisitions exceed active stock."
    )
    
    construction_inspection_strict = fields.Boolean(
        string='Strict Inspection Billing',
        config_parameter='construction_erp.inspection_strict',
        default=True,
        help="Subcontractor Vendor Bills are strictly gated until linked QA Inspections pass."
    )
    
    construction_default_scrap_location_id = fields.Many2one(
        'stock.location',
        string='Default Scrap Location',
        config_parameter='construction_erp.default_scrap_location_id',
        domain="[('scrap_location', '=', True)]",
        help="The specific virtual location ruined materials are routed to."
    )

    # Twilio / WhatsApp Settings
    twilio_account_sid = fields.Char(string='Twilio Account SID', config_parameter='construction_erp.twilio_account_sid')
    twilio_auth_token = fields.Char(string='Twilio Auth Token', config_parameter='construction_erp.twilio_auth_token')
    twilio_from_number = fields.Char(string='Twilio From Number (WhatsApp)', config_parameter='construction_erp.twilio_from_number', help="e.g., whatsapp:+14155238886")

    # Telegram Settings
    telegram_bot_token = fields.Char(string='Telegram Bot Token', config_parameter='construction_erp.telegram_bot_token')

    # Reminder Throttling
    reminder_interval_days = fields.Integer(string='Reminder Interval (Days)', config_parameter='construction_erp.reminder_interval_days', default=7)
    max_reminder_limit = fields.Integer(string='Max Reminders per Installment', config_parameter='construction_erp.max_reminder_limit', default=3)

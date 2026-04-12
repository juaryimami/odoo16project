# -*- coding: utf-8 -*-
from odoo import models, fields

class Partner(models.Model):
    _inherit = 'res.partner'

    is_contractor = fields.Boolean(string='Is a Contractor')
    is_client = fields.Boolean(string='Is a Client')
    receipt_upload_pin = fields.Char(string='Receipt Upload PIN', help='A secret PIN the client must enter to upload payment receipts.', copy=False)
    telegram_chat_id = fields.Char(string='Telegram Chat ID', help='The numerical ID required for the Telegram Bot API to message this partner.')

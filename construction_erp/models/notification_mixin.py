# -*- coding: utf-8 -*-
import logging
import requests
from requests.auth import HTTPBasicAuth
from odoo import models, api, _

_logger = logging.getLogger(__name__)

class NotificationMixin(models.AbstractModel):
    _name = 'construction.notification.mixin'
    _description = 'Unified Communication Gateway Mixin'

    def _send_whatsapp_notification(self, partner, message):
        """ Sends a WhatsApp message via Twilio API. """
        params = self.env['ir.config_parameter'].sudo()
        sid = params.get_param('construction_erp.twilio_account_sid')
        token = params.get_param('construction_erp.twilio_auth_token')
        from_phone = params.get_param('construction_erp.twilio_from_number')
        
        if not (sid and token and from_phone and partner.phone):
            _logger.info("Missing WhatsApp configuration or partner phone.")
            return False

        try:
            to_number = f"whatsapp:{partner.phone}"
            from_number = from_phone if from_phone.startswith('whatsapp:') else f"whatsapp:{from_phone}"
            
            response = requests.post(
                f"https://api.twilio.org/2010-04-01/Accounts/{sid}/Messages.json",
                auth=HTTPBasicAuth(sid, token),
                data={'To': to_number, 'From': from_number, 'Body': message},
                timeout=10
            )
            if response.status_code in [200, 201]:
                return True
            _logger.error(f"WhatsApp Error: {response.text}")
        except Exception as e:
            _logger.exception(f"WhatsApp Request Failed: {e}")
        return False

    def _send_telegram_notification(self, partner, message):
        """ Sends a Telegram message via Bot API. """
        params = self.env['ir.config_parameter'].sudo()
        token = params.get_param('construction_erp.telegram_bot_token')
        
        if not (token and partner.telegram_chat_id):
            _logger.info("Missing Telegram configuration or partner chat ID.")
            return False

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            response = requests.post(
                url, 
                json={'chat_id': partner.telegram_chat_id, 'text': message},
                timeout=10
            )
            if response.status_code == 200:
                return True
            _logger.error(f"Telegram Error: {response.text}")
        except Exception as e:
            _logger.exception(f"Telegram Request Failed: {e}")
        return False

    def notify_contact(self, partner, message, title=None):
        """ High-level method to notify a contact via all active channels. """
        channels_used = []
        if self._send_whatsapp_notification(partner, message):
            channels_used.append("WhatsApp")
        if self._send_telegram_notification(partner, message):
            channels_used.append("Telegram")
        
        if channels_used:
            body = _("<b>Instant Notification Sent</b> via %s") % (", ".join(channels_used))
            if title:
                body = f"<b>{title}</b><br/>{body}"
            self.message_post(body=body)
        return bool(channels_used)

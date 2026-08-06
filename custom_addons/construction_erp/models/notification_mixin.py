# -*- coding: utf-8 -*-
import logging
import requests
import json
import html
from requests.auth import HTTPBasicAuth
# pyrefly: ignore [missing-import]
from odoo import models, api, _

_logger = logging.getLogger(__name__)

class NotificationMixin(models.AbstractModel):
    _name = 'construction.notification.mixin'
    _description = 'Unified Communication Gateway Mixin'

    def _send_whatsapp_notification(self, partner, message, template_sid=None, template_variables=None):
        """ Sends a WhatsApp message via Twilio API (Supports Text or Templates). """
        params = self.env['ir.config_parameter'].sudo()
        sid = params.get_param('construction_erp.twilio_account_sid')
        token = params.get_param('construction_erp.twilio_auth_token')
        from_phone = params.get_param('construction_erp.twilio_from_number')
        
        to_phone = partner.whatsapp_number or partner.phone or partner.mobile
        
        if not (sid and token and from_phone and to_phone):
            _logger.info("Missing WhatsApp configuration or partner phone for %s", partner.name)
            return False

        try:
            clean_phone = "".join(c for c in to_phone if c.isdigit() or c == "+")
            to_number = f"whatsapp:{clean_phone}"
            from_number = from_phone if from_phone.startswith('whatsapp:') else f"whatsapp:{from_phone}"
            
            # Prepare Payload
            payload = {'To': to_number, 'From': from_number}
            
            if template_sid:
                payload['ContentSid'] = template_sid
                if template_variables:
                    payload['ContentVariables'] = json.dumps(template_variables)
                _logger.info("Twilio Template Request: To=%s, ContentSid=%s", to_number, template_sid)
            else:
                payload['Body'] = message
                _logger.info("Twilio Text Request: To=%s, From=%s", to_number, from_number)
            
            response = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                auth=HTTPBasicAuth(sid, token),
                data=payload,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                _logger.info("WhatsApp message sent successfully to %s", partner.name)
                return True
            _logger.error(f"WhatsApp Error Response: {response.status_code} - {response.text}")
        except Exception as e:
            _logger.exception(f"WhatsApp Request Failed for {partner.name}: {e}")
        return False

    def _send_telegram_notification(self, partner, message, reply_markup=None):
        """ Sends a Telegram message via Bot API with HTML support and action buttons. """
        params = self.env['ir.config_parameter'].sudo()
        token = params.get_param('construction_erp.telegram_bot_token')
        
        if not (token and partner.telegram_chat_id):
            _logger.info("Missing Telegram configuration or partner chat ID.")
            return False

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            payload = {
                'chat_id': partner.telegram_chat_id, 
                'text': message,
                'parse_mode': 'HTML'
            }
            # Telegram expects reply_markup to be a JSON string
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            _logger.info(f"Sending Telegram Message to {partner.name} (Chat ID: {partner.telegram_chat_id})")
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            
            _logger.error(f"Telegram API Error: {response.status_code} - {response.text}")
            # Fallback to plain text if HTML fails
            if response.status_code != 200:
                payload['parse_mode'] = ''
                payload['text'] = html.escape(message)
                response = requests.post(url, json=payload, timeout=10)
                return response.status_code == 200

        except Exception as e:
            _logger.exception(f"Telegram Request Failed: {e}")
        return False

    def send_in_app_notification(self, user, message, title=None):
        """ Creates a mail activity for the user as an in-app notification. """
        if not user:
            return False
        
        try:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=title or _('Construction Alert'),
                note=message
            )
            return True
        except Exception as e:
            _logger.warning(f"Could not send in-app notification to {user.name}: {e}")
            return False

    def notify_contact(self, partner, message, title=None, reply_markup=None, template_sid=None, template_variables=None):
        """ High-level method to notify a contact via their preferred channel. """
        channels_used = []
        pref = partner.notification_preference
        
        if pref == 'whatsapp' or not pref: # Default or WhatsApp
            if self._send_whatsapp_notification(partner, message, template_sid=template_sid, template_variables=template_variables):
                channels_used.append("WhatsApp")
        
        if pref == 'telegram':
            if self._send_telegram_notification(partner, message, reply_markup=reply_markup):
                channels_used.append("Telegram")
        
        if channels_used:
            body = _("<b>Instant Notification Sent</b> via %s") % (", ".join(channels_used))
            if title:
                body = f"<b>{title}</b><br/>{body}"
            self.message_post(body=body)
        return bool(channels_used)

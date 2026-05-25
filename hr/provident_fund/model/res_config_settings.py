from odoo import models, _, fields, api

class BalanceCheck(models.TransientModel):
    _inherit = 'res.config.settings'

    allowed_percent = fields.Float(string="Allowed to withdraw",config_parameter="provident_fund.allowed_percent")



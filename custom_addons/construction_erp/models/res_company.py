# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    construction_logo = fields.Binary(string="Construction Logo", help="Logo used for construction reports and dashboards.")

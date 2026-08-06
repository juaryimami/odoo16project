# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tin_number = fields.Char(string='TIN Number', groups="hr.group_hr_user", tracking=True)
    pension_number = fields.Char(string='Pension Number', groups="hr.group_hr_user", tracking=True)

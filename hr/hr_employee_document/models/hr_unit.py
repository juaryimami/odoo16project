from odoo import fields, models


class HRUnit(models.Model):
    _name = 'hr.unit'
    _description = 'HR Unit'
    _rec_name = 'unit'

    unit = fields.Char(string='Unit', required=True)
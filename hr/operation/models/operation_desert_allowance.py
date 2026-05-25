from odoo import models, fields, api
from datetime import date


class OperationAllowance(models.Model):
    _name = 'operation.desert.allowance'
    _description = 'Desert Allowance'
    _rec_name='rate'

    rate = fields.Float(string='Rate(%)', required=True)
    description = fields.Text(string='Description')


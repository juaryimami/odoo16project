from odoo import api, fields, models, _
from datetime import datetime

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    need_pen = fields.Boolean(string="Create PEN", default=False )
    identification_id = fields.Char(string="PEN",  required=True, copy=False, default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('need_pen'):
            if vals.get('identification_id', ('New')) == _('New'):
                vals['identification_id'] = self.env['ir.sequence'].next_by_code('hr.employee') or _('New')
        res = super(HREmployee, self).create(vals)
        return res

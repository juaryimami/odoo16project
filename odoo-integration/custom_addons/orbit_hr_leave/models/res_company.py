from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    probation_working_days = fields.Integer(
        string="Default Probation Working Days",
        default=45,
        help="Default number of working days for employee probation period."
    )

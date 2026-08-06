from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    probation_working_days = fields.Integer(
        related='company_id.probation_working_days',
        readonly=False,
        string="Default Probation Working Days"
    )

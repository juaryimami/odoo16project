from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HrPayrollRequestForm(models.TransientModel):
    _name = 'hr.payroll.request.form'
    _description = 'Hr Payroll Request form'
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    currency_type = fields.Selection([
        ('etb', 'ETB'),
        ('usd', 'USD'),
        ('eur', 'EUR'),
        ('gbp', 'GBP'),
    ], string='Currency Type', default='etb', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string="Department")
    # project_id = fields.Many2one('agent.project', string="Project")
    exch_rate=fields.Float("Exchange Rate")

    def compute_and_open_payroll_report(self):
        for rec in self:
            self.env['custom.hr.payroll.report'].search([]).unlink()
            self.env['custom.hr.payroll.report'].fetch_and_update_report(rec.date_from, rec.date_to, rec.department_id)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Custom Payroll Report',
                'res_model': 'custom.hr.payroll.report',
                'view_mode': 'tree',
                'target': 'current',
            }


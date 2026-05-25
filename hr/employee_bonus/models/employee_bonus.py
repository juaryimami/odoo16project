from odoo import fields, models,_, api
class EmployeeBonus(models.Model):
    _name = "employee.bonus"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(string="Reference")
    reason = fields.Text(string="Reason")
    effective_date = fields.Date(string="Effective date")
    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True)
    approved_by = fields.Many2one('res.users', string="Approved by", required=True, tracking=True)
    approved_date = fields.Date(string="Approved date", required=True)
    bonus_type = fields.Selection([('percent', 'Percent'), ('fixed', 'Fixed')], string="Bonus Type",
                                      default="percent", required=True, tracking=True, )
    percent_amount = fields.Float(string="Amount in percent", tracking=True, required=True)
    fixed_amount = fields.Float(string="Fixed Amount", tracking=True, required=True)

    value = fields.Float(string="Value", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency")
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted'), ('reject', 'Rejected'), ('approve', 'Approved'),
         ('validate', 'Validated'), ('in_payment', 'In Payment'),('paid', 'Paid')], default="draft")
    type_id = fields.Many2one('bonus.type', string="Bonus type", required=True, tracking=True)

    def action_submit(self):
        self.state = "submit"

    def action_reject(self):
        self.state = "reject"

    def action_approve(self):
        self.state = "approve"

    def action_validate(self):

        self.state = "validate"

    def action_paid(self):
        self.state = 'paid'

    @api.depends('employee_id','bonus_type','fixed_amount','percent_amount')
    def compute_value(self):
        if self.employee_id:
            for rec in self.employee_id:
                salary = self.env['hr.contract'].search([('employee_id', '=', rec.id)])
                for s in salary:
                    if self.bonus_type == 'percent' and self.percent_amount:
                        s_rate = self.percent_amount * s.wage / 100
                        self.write({'value': s_rate})
                    if self.bonus_type == 'fixed' and self.fixed_amount:
                        fix = self.fixed_amount
                        self.write({'value': fix})
        self.state = 'in_payment'


class BonusType(models.Model):
    _name = 'bonus.type'

    name = fields.Char(string="Bonus Type", required=True)

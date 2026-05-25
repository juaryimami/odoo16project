from odoo import models, _, fields, api
from odoo.exceptions import ValidationError

class ProvidentFund(models.Model):
    _name = 'provident.fund'
    _description = 'Ethiopian Provident fund'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    employee_id = fields.Many2one('hr.employee', required=True)
    request_date = fields.Date(string='Requestd Date', required=True)
    request_amount = fields.Float(string="Requested Amount", required=True)
    balance_amount = fields.Float(string='Remaining Balance', compute = '_compute_balance', store=True,default=False)
    confirm_by = fields.Many2one('hr.employee',string="Confirmed by", required=False)
    confirm_date = fields.Date(required=False, string="Confirm Date")

    validated_by = fields.Many2one('hr.employee', string="Validated by", required=False)
    validated_date = fields.Date(required=False, string="Validated Date")

    approved_by = fields.Many2one('hr.employee',string="Approved by", required=False)
    approved_date = fields.Date(required=False, string="Approved Date")



    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit','Submitted'),
        ('confirm','Confirmed'),
        ('validate', 'Validated'),
        ('approve','Approved'),
        ('reset','Reset'),
         ('reject','Reject'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def action_submit(self):
        for rec in self:
            rec.state = 'submit'
            users = self.env.ref('provident_fund.provident_group_user').users
            for user in users:
                activity_type = self.env.ref('provident_fund.mail_activity_provident_approved')
                self.activity_schedule('provident_fund.mail_activity_provident_approved', user_id = user.id,
                                       note=f"please validate provident for {self.employee_id.name}")

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

            users = self.env.ref('provident_fund.provident_group_supervisor').users
            for user in users:
                activity_type = self.env.ref('provident_fund.mail_activity_provident_approved')
                self.activity_schedule('provident_fund.mail_activity_provident_approved', user_id=user.id,
                                       note=f"please validate provident for {self.employee_id.name}")

    def action_validate(self):
        for rec in self:
            rec.state = 'validate'

            users = self.env.ref('provident_fund.provident_group_finance_manager').users
            for user in users:
                activity_type = self.env.ref('provident_fund.mail_activity_provident_approved')
                self.activity_schedule('provident_fund.mail_activity_provident_approved', user_id=user.id,
                                       note=f"please validate provident for {self.employee_id.name}")

    # @api.depends('employee_id')
    def action_approve(self):
        for rec in self:
            rec.state = 'approve'

            users = self.env.ref('provident_fund.provident_group_executive_director').users
            for user in users:
                activity_type = self.env.ref('provident_fund.mail_activity_provident_approved')
                self.activity_schedule('provident_fund.mail_activity_provident_approved', user_id=user.id,
                                       note=f"please validate provident for {self.employee_id.name}")

        mail_template = self.env.ref('provident_fund.provident_fund_email_template')
        mail_template.send_mail(self.id, force_send=True)

        self.balance_amount = self._compute_balance()





    def action_reject(self):
        for rec in self:
            rec.state = 'reject'

            users = self.env.ref('provident_fund.provident_group_executive_director').users
            for user in users:
                activity_type = self.env.ref('provident_fund.mail_activity_provident_approved')
                self.activity_schedule('provident_fund.mail_activity_provident_approved', user_id=user.id,
                                       note=f"Provident fund is rejected for {self.employee_id.name}")

        mail_template = self.env.ref('provident_fund.provident_fund_reject_email_template')
        mail_template.send_mail(self.id, force_send=True)

        self.balance_amount = self._compute_balance()

    def action_reset(self):
        for rec in self:
            rec.state = 'draft'

    def action_send_email(self):
        mail_template =self.env.ref('provident_fund.model_provident_fund')
        mail_template.send_mail(self.id, force_send=True)
    @api.depends('employee_id')
    def _compute_balance(self):

           employer_balance = 0.0
           employee_balance = 0
           total_request = 0.0
           initial = self.env['provident.initial'].search([('employee_id', '=', self.employee_id.id)])
           for request in self.env['provident.fund'].search([('employee_id','=',self.employee_id.id)]):
               total_request += request.request_amount
           for payslip in self.env['hr.payslip.line'].search([('employee_id','=',self.employee_id.id)]):
               if payslip.code == 'EMPR':
                 employee_balance += payslip.amount
               if payslip.code == 'EPRNT':
                 employer_balance += payslip.amount


           total_balance = employee_balance + employer_balance + initial.initial_balance
           return total_balance - total_request



    @api.model
    def create(self, vals):
        employer_balance = 0.0
        employee_balance = 0
        total_request = 0.0
        total_balance = 0.0
        initial = self.env['provident.initial'].search([('employee_id','=',vals['employee_id'])])
        # print('printing...', initial.initial_balance)
        for request in self.env['provident.fund'].search([('employee_id', '=', vals['employee_id'])]):
            total_request += request.request_amount
        for payslip in self.env['hr.payslip.line'].search(
                [('employee_id', '=', vals['employee_id'])]):
            if payslip.code == 'EMPR':
                employee_balance += payslip.amount
            if payslip.code == 'EPRNT':
                employer_balance += payslip.amount
        # print('printing...', initial.initial_balance)
        # if employer_balance and employee_balance:
        total_balance = employee_balance + employer_balance + initial.initial_balance
        # else:
        #     total_balance = initial.initial_balance
        remaining_balance = total_balance - total_request
        requested_inpercent = float(vals['request_amount']) / remaining_balance * 100
        allowed_percent = float(self.env['ir.config_parameter'].get_param('provident_fund.allowed_percent'))
        if requested_inpercent <= allowed_percent:
            return super(ProvidentFund, self).create(vals)
        elif requested_inpercent > allowed_percent:
            raise ValidationError('Requested provident fund is more than ' + str(allowed_percent) + ' % of total balance')


class EmployeeFundInitial(models.Model):
    _name = 'provident.initial'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    employee_id = fields.Many2one('hr.employee', required=True)
    initial_balance = fields.Float(string="Initial Balance")
    date_from  = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date From", required=True)
    description = fields.Text(string="Description")
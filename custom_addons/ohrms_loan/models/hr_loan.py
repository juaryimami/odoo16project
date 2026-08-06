# -*- coding: utf-8 -*-

# from odoo import models, fields, api, _
# from datetime import datetime
# from dateutil.relativedelta import relativedelta
# from odoo.exceptions import ValidationError, UserError
#
#
# class HrLoan(models.Model):
#     _name = 'hr.loan'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _description = "Loan Request"
#
#     @api.model
#     def default_get(self, field_list):
#         result = super(HrLoan, self).default_get(field_list)
#         if result.get('user_id'):
#             ts_user_id = result['user_id']
#         else:
#             ts_user_id = self.env.context.get('user_id', self.env.user.id)
#         result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
#         return result
#
#     def _compute_loan_amount(self):
#         total_paid = 0.0
#         for loan in self:
#             for line in loan.loan_lines:
#                 if line.paid:
#                     total_paid += line.amount
#             balance_amount = loan.loan_amount - total_paid
#             loan.total_amount = loan.loan_amount
#             loan.balance_amount = balance_amount
#             loan.total_paid_amount = total_paid
#
#     name = fields.Char(string="Loan Name", default="/", readonly=True, help="Name of the loan")
#     date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
#     employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
#     department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
#                                     string="Department", help="Employee")
#     installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
#     payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of "
#                                                                                                              "the "
#                                                                                                              "paymemt")
#     loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
#     company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
#                                  default=lambda self: self.env.user.company_id,
#                                  states={'draft': [('readonly', False)]})
#     currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
#                                   default=lambda self: self.env.user.company_id.currency_id)
#     job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
#                                    help="Job position")
#     loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
#     total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
#                                 help="Total loan amount")
#     balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount', help="Balance amount")
#     total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_loan_amount',
#                                      help="Total paid amount")
#
#     checked_by = fields.Many2one('hr.employee', string="Checked By")
#     checked_date = fields.Date(string="Checked date")
#
#     approved_by = fields.Many2one('hr.employee', string="Approved By")
#     approved_date = fields.Date(string="Approved date")
#
#     receipt = fields.Float(string='Cash Receipt')
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('waiting_approval_1', 'Submitted'),
#         ('check','Checked'),
#         ('approve', 'Approved'),
#         ('refuse', 'Refused'),
#         # ('draft', 'Reset'),
#     ], string="State", default='draft', track_visibility='onchange', copy=False, )
#
#     @api.model
#     def create(self, values):
#
#         if values['receipt']:
#             self._compute_loan_amount()
#         loan_count = self.env['hr.loan'].search_count(
#             [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
#              ('balance_amount', '!=', 0)])
#         if loan_count:
#
#             raise ValidationError(_("The employee has already a pending installment"))
#         else:
#             values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
#             res = super(HrLoan, self).create(values)
#             return res
#
#     def compute_installment(self):
#         """This automatically create the installment the employee need to pay to
#         company based on payment start date and the no of installments.
#             """
#         for loan in self:
#             loan.loan_lines.unlink()
#             date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
#             amount = loan.loan_amount / loan.installment
#             for i in range(1, loan.installment + 1):
#                 self.env['hr.loan.line'].create({
#                     'date': date_start,
#                     'amount': amount,
#                     'employee_id': loan.employee_id.id,
#                     'loan_id': loan.id})
#                 date_start = date_start + relativedelta(months=1)
#             loan._compute_loan_amount()
#         return True
#
#     def action_check(self):
#         for rec in self:
#             rec.state = "check"
#             users = self.env.ref('ohrms_loan.loan_group_approver').users
#             for user in users:
#                 activity_type = self.env.ref('ohrms_loan.mail_activity_loan_advance')
#                 self.activity_schedule('ohrms_loan.mail_activity_loan_advance', user_id=user.id,
#                                        note=f"please approve loan/advance for {self.employee_id.name}")
#         mail_template = self.env.ref('ohrms_loan.loan_advance_email_template')
#         mail_template.send_mail(self.id, force_send=True)
#
#     def action_refuse(self):
#         return self.write({'state': 'refuse'})
#
#     def action_submit(self):
#         self.write({'state': 'waiting_approval_1'})
#         users = self.env.ref('ohrms_loan.loan_group_manager').users
#         for user in users:
#             activity_type = self.env.ref('ohrms_loan.mail_activity_loan_advance')
#             self.activity_schedule('ohrms_loan.mail_activity_loan_advance', user_id=user.id,
#                                    note=f"please approve loan/advance for {self.employee_id.name}")
#
#         mail_template = self.env.ref('ohrms_loan.loan_advance_email_template')
#         mail_template.send_mail(self.id, force_send=True)
#
#     # def action_reset(self):
#     #     self.write({'state': 'draft'})
#
#     def action_approve(self):
#         for data in self:
#             if not data.loan_lines:
#                 raise ValidationError(_("Please Compute installment"))
#             else:
#                 self.write({'state': 'approve'})
#                 users = self.env.ref('ohrms_loan.loan_group_approver').users
#                 for user in users:
#                     activity_type = self.env.ref('ohrms_loan.mail_activity_loan_advance')
#                     self.activity_schedule('ohrms_loan.mail_activity_loan_advance', user_id=user.id,
#                                            note=f"your loan/advance is approved {self.employee_id.name}")
#
#                 mail_template = self.env.ref('ohrms_loan.loan_advance_email_template')
#                 mail_template.send_mail(self.id, force_send=True)
#
#     def unlink(self):
#         for loan in self:
#             if loan.state not in ('draft', 'cancel'):
#                 raise UserError(
#                     'You cannot delete a loan which is not in draft or cancelled state')
#         return super(HrLoan, self).unlink()
#
#
# class InstallmentLine(models.Model):
#     _name = "hr.loan.line"
#     _description = "Installment Line"
#
#     date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
#     employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
#     amount = fields.Float(string="Amount", required=True, help="Amount")
#     paid = fields.Boolean(string="Paid", help="Paid")
#     loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
#     payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")
#
#
# class HrEmployee(models.Model):
#     _inherit = "hr.employee"
#
#     def _compute_employee_loans(self):
#         """This compute the loan amount and total loans count of an employee.
#             """
#         self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])
#
#     loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.total_amount1 - total_paid
            loan.total_amount = loan.total_amount1
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    checked_by = fields.Many2one('res.users', string="Checked By")
    checked_date = fields.Date(string="Checked date")

    approved_by = fields.Many2one('res.users', string="Approved By")
    approved_date = fields.Date(string="Approved date")
    name = fields.Char(string="Loan Name", default="/", readonly=True, help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of "
                                                                                                             "the "
                                                                                                             "paymemt")
    end_date = fields.Date(string="Payment Start Date", default=fields.Date.today())
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
                                   help="Job position")
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    interest_rate = fields.Float(string="Interest Rate")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    total_amount1 = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount_total',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount', help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_loan_amount',
                                     help="Total paid amount")

    term_payment = fields.Float(store=True, readonly=True, compute='_compute_loan_amount_total')



    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('refuse', 'Check'),
        ('cancel', 'Canceled'),
        ('approve', 'Approved'),        
        
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    payment_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi Annually'),
        ('annually', 'Annually'),
    ], string="Payment Cycle", default='monthly')

    attachment=fields.Binary(string="Attachment")

    @api.depends('loan_amount','interest_rate','installment')
    def _compute_loan_amount_total(self):
        for rec in self:
            if rec.installment:
                rec.term_payment= rec.total_amount1/rec.installment
            else:
                rec.term_payment=rec.total_amount1

            if rec.interest_rate:
                rec.total_amount1 =rec.loan_amount + rec.loan_amount* rec.interest_rate/100
            else:
                rec.total_amount1=rec.loan_amount



    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=',self.employee_id.id), ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    # def compute_installment(self):
    #     """This automatically create the installment the employee need to pay to
    #     company based on payment start date and the no of installments.
    #         """
    #     for loan in self:
    #         loan.loan_lines.unlink()
    #         date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
    #         amount = loan.loan_amount / loan.installment
    #         for i in range(1, loan.installment + 1):
    #             self.env['hr.loan.line'].create({
    #                 'date': date_start,
    #                 'amount': amount,
    #                 'employee_id': loan.employee_id.id,
    #                 'loan_id': loan.id})
    #             date_start = date_start + relativedelta(months=1)
    #         loan._compute_loan_amount()
    #     return True
    #
    # def action_refuse(self):
    #     return self.write({'state': 'refuse'})
    #
    # def action_submit(self):
    #     self.write({'state': 'waiting_approval_1'})
    #
    def action_cancel(self):
        self.write({'state': 'cancel'})

    def compute_installment(self):
            """This automatically create the installment the employee need to pay to
            company based on payment start date and the no of installments.
                """
            for loan in self:
                if loan.payment_cycle=="quarterly":
                    months=4
                elif loan.payment_cycle=="semi_annually":
                    months = 6
                elif loan.payment_cycle=="annually":
                    months = 12
                else:
                    months = 1
                loan.loan_lines.unlink()
                date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
                amount = loan.total_amount1 / loan.installment
                for i in range(1, loan.installment + 1):
                    self.env['hr.loan.line'].create({
                        'date': date_start,
                        'amount': amount,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})

                    date_start = date_start + relativedelta(months=months)
                loan.end_date=date_start
                loan._compute_loan_amount()
            return True

    def action_check(self):
            for rec in self:
                rec.state = "check"
                users = self.env.ref('ohrms_loan.loan_group_approver').users
                for user in users:
                    activity_type = self.env.ref('ohrms_loan.mail_activity_loan_advance')
                    self.activity_schedule('ohrms_loan.mail_activity_loan_advance', user_id=user.id,
                                           note=f"please approve loan/advance for {self.employee_id.name}")
            mail_template = self.env.ref('ohrms_loan.loan_advance_email_template_id')
            mail_template.send_mail(self.id, force_send=True)

    def action_refuse(self):
        current_user = self.env.user
        return self.write({'state': 'refuse','checked_by':current_user.id,'checked_date':datetime.now()})


    def action_submit(self):
            self.write({'state': 'waiting_approval_1'})
            users = self.env.ref('ohrms_loan.loan_group_manager').users
            for user in users:
                activity_type = self.env.ref('ohrms_loan.mail_activity_loan_advance')
                self.activity_schedule('ohrms_loan.mail_activity_loan_advance', user_id=user.id,
                                       note=f"please approve loan/advance for {self.employee_id.name}")

            mail_template = self.env.ref('ohrms_loan.loan_advance_email_template_id')
            mail_template.send_mail(self.id, force_send=True)

        # def action_reset(self):
        #     self.write({'state': 'draft'})



    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                current_user = self.env.user
                self.write({'state': 'approve', 'approved_by':current_user.id, 'approved_date':self.approved_date})

        def action_approve(self):
            for data in self:
                if not data.loan_lines:
                    raise ValidationError(_("Please Compute installment"))
                else:
                    self.write({'state': 'approve'})
                    users = self.env.ref('ohrms_loan.loan_group_approver').users
                    for user in users:
                        activity_type = self.env.ref('ohrms_loan.mail_activity_loan_advance')
                        self.activity_schedule('ohrms_loan.mail_activity_loan_advance', user_id=user.id,
                                               note=f"your loan/advance is approved {self.employee_id.name}")

                    mail_template = self.env.ref('ohrms_loan.loan_advance_email_template_id')
                    mail_template.send_mail(self.id, force_send=True)

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        for rec in self:
            rec.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', rec.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
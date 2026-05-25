import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class customHrPayrollReport(models.TransientModel):
    _name = "custom.hr.payroll.report"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Payroll Report"

    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    employee = fields.Char(string="Employee")
    department_id = fields.Many2one('hr.department', string="Department")
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account")
    period = fields.Char(string="Period")
    monthly_basic_salary = fields.Float(string="Monthly Basic Salary")
    total_working_days = fields.Float(string="Total Working Days", digits=(4, 2))
    total_day_worked = fields.Float(string="Total Day Worked",digits=(4, 2))
    payslip_run_name = fields.Char(string="Month Of Payroll")
    structure = fields.Char(string="Structure")
    payslip_name = fields.Char(string="Payslip Name")
    basic = fields.Float(string="BASIC")
    basic_etb = fields.Float(string="BASIC")
    gross = fields.Float(string="GROSS")
    net = fields.Float(string="NET")
    pension = fields.Float(string="Employee Pension (7%)")
    pension_comp = fields.Float(string="Employer Pension(11%)")
    tax = fields.Float(string="Income Tax")
    total_deduction = fields.Float(string="Total Deduction")
    overtime = fields.Float(string="Overtime")
    hra = fields.Float(string="House Rent Allowance")
    da = fields.Float(string="Position Allowance")
    travel_allowance = fields.Float(string="Transport Allowance")
    travel_allowance_notax = fields.Float(string="None Taxable Transport Allowance")
    meal_allowance = fields.Float(string="Provision For Leave")
    medical_allowance = fields.Float(string="Medical Insurance")
    communication_allowance = fields.Float(string="Communication Allowance")
    internet_allowance = fields.Float(string="Internet Allowance")
    fuel_allowance = fields.Float(string="Fuel Allowance")
    unused_leave_payment = fields.Float(string="Unused Leave Payment")
    severance_pay_compensation = fields.Float(string="Severance Pay Compensation")
    training_development = fields.Float(string="Training And Development")
    position_allowance = fields.Float(string="Position Allowance")
    desert_allowance = fields.Float(string="Desert Allowance")
    representation_allowance = fields.Float(string="Representation Allowance")
    taxable_salary = fields.Float(string="Taxable Salary")
    total_payment = fields.Float(string="Severance net payment ")
    total_adjusted_payout = fields.Float(string="Severance TAX payment ")
    expense = fields.Float(string="Expense")
    loan = fields.Float(string="Loan")
    advance_salary = fields.Float(string="Advance Salary")
    bonus = fields.Float(string="Bonus")
    status = fields.Char(string="Status")
    updated_on = fields.Datetime(string="Updated On")
    created_on = fields.Datetime(string="Created Date")
    last_updated = fields.Datetime(string="Last Updated")
    provident_employee = fields.Float(string="Employee Provident Fund")
    provident_employer = fields.Float(string="Employer Provident Fund")
    total_provident = fields.Float(string="Total Provident Fund")


    def print_pdf_report(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Report',
            'res_model': 'hr.payroll.report1',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payroll_ids': self.ids,
            }
        }



    def fetch_and_update_report(self, date_from, date_to, department_id):
        last_update = datetime.datetime.now()
        default_company = self.env.user.company_id

        domain = ['|', ('company_id', '=', False), ('company_id', '=', default_company.id)]

        if date_from and date_to:
            domain += [('date_from', '>=', date_from), ('date_to', '<=', date_to)]

        if department_id:
            domain.append(('employee_id.department_id', '=', department_id.id))

        payslips = self.env['hr.payslip'].search(domain, order='write_date desc')

        if len(payslips) > 0:
            last_update = payslips[0].write_date
        for pays in payslips:
            payroll_amount = self.update_payslips(pays.line_ids)
            contract = pays.employee_id.contract_id
            working_days =0,0
            total_worked_days=0
            if date_from and date_to:
                working_days = self.env['hr.attendance'].calculate_working_days(date_from, date_to,
                                                                                contract.resource_calendar_id)
                total_worked_days = self.env['hr.attendance'].compute_worked_days(pays.employee_id, date_from, date_to,
                                                                                  working_days[1])
                if working_days[0] < total_worked_days:
                    total_worked_days = working_days[0]


            report_row = {
                'payslip_id': pays.id,
                'employee': pays.employee_id.name,
                'department_id': pays.employee_id.department_id.id,
                'payslip_run_name': pays.name,
                'monthly_basic_salary':contract.wage,
                'total_working_days':working_days[0],
                'total_day_worked':total_worked_days,
                'bank_account_id': pays.employee_id.bank_account_id.id,
                'structure': pays.struct_id.name,
                'period': pays.date_from.strftime('%Y-%m-%d') + " - " + pays.date_to.strftime('%Y-%m-%d'),
                'payslip_name': pays.number,
                'basic': payroll_amount["basic"],
                'basic_etb': payroll_amount["basic_etb"],
                'taxable_salary': payroll_amount["taxable_salary"],
                'total_deduction': payroll_amount["total_deduction"],
                'gross': payroll_amount["gross"],
                'net': payroll_amount["net"],
                'pension': payroll_amount["pension"],
                'pension_comp': payroll_amount["pension_comp"],
                'tax': payroll_amount["tax"],
                'overtime': payroll_amount["overtime"],
                'hra': payroll_amount["hra"],
                'da': payroll_amount["da"],
                'travel_allowance': payroll_amount["travel_allowance"],
                'travel_allowance_notax': payroll_amount["travel_allowance_notax"],
                'meal_allowance': payroll_amount["meal_allowance"],
                'medical_allowance': payroll_amount["medical_allowance"],
                'communication_allowance': payroll_amount["communication_allowance"],
                'internet_allowance': payroll_amount["internet_allowance"],
                'fuel_allowance': payroll_amount["fuel_allowance"],
                'unused_leave_payment': payroll_amount["unused_leave_payment"],
                'severance_pay_compensation': payroll_amount["severance_pay_compensation"],
                'training_development': payroll_amount["training_development"],
                'position_allowance': payroll_amount["position_allowance"],
                'desert_allowance': payroll_amount["desert_allowance"],
                'representation_allowance': payroll_amount["representation_allowance"],
                'total_payment': payroll_amount["total_payment"],
                'total_adjusted_payout': payroll_amount["total_adjusted_payout"],
                'expense': payroll_amount["expense"],
                'loan': payroll_amount["loan"],
                'advance_salary': payroll_amount["advance_salary"],
                'bonus': payroll_amount["bonus"],
                'provident_employee': payroll_amount["provident_employee"],
                'provident_employer': payroll_amount["provident_employer"],
                'total_provident': payroll_amount["provident_employee"] + payroll_amount["provident_employer"],
                'status': pays.state,
                'created_on': pays.create_date,
                'updated_on': pays.write_date,
                'last_updated': last_update,
            }
            self.env['custom.hr.payroll.report'].sudo().create(report_row)


    def refresh_report(self):
        self.env['hr.payslip'].search([]).unlink()
        self.fetch_and_update_report()

    def confirm_payslip_status(self):
        for rec in self:
            self.env['hr.payslip'].search([('id', '=', rec.payslip_id.id)]).action_payslip_done()

    def return_payslip_detail(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Payslip',
                'res_model': 'hr.payslip',
                'view_mode': 'form,tree',
                'target': 'current',
                'res_id': rec.payslip_id.id,
                'context': {
                    'default_id': rec.payslip_id.id,
                }
            }

    def update_payslips(self, payslip_lines):
        payroll_amount = {
            "basic": 0.0,
            "basic_etb": 0.0,
            "taxable_salary": 0.0,
            "gross": 0.0,
            "net": 0.0,
            "pension": 0.0,
            "pension_comp": 0.0,
            "tax": 0.0,
            "total_deduction": 0.0,
            "overtime": 0.0,
            "hra": 0.0,
            "da": 0.0,
            "travel_allowance": 0.0,
            "travel_allowance_notax": 0.0,
            "meal_allowance": 0.0,
            "medical_allowance": 0.0,
            "communication_allowance": 0.0,
            "internet_allowance": 0.0,
            "fuel_allowance": 0.0,
            "unused_leave_payment": 0.0,
            "severance_pay_compensation": 0.0,
            "training_development": 0.0,
            "position_allowance": 0.0,
            "desert_allowance": 0.0,
            "representation_allowance": 0.0,
            "total_payment":0.0,
            "total_adjusted_payout":0.0,
            "expense": 0.0,
            "loan": 0.0,
            "advance_salary": 0.0,
            "bonus": 0.0,
            "provident_employee": 0.0,
            "provident_employer": 0.0,
            "total_provident": 0.0,
        }
        for line in payslip_lines:
            if line.code == 'BASIC':
                payroll_amount["basic"] = line.amount
                payroll_amount["basic_etb"] = line.amount
            elif line.code == 'TTI':
                payroll_amount["taxable_salary"] = line.amount
            elif line.code == 'GROSS':
                payroll_amount["gross"] = line.amount
            elif line.code == 'NET':
                payroll_amount["net"] = line.amount
            elif line.code == 'PENSION':
                payroll_amount["pension"] = line.amount
            elif line.code == 'COMPPENSION':
                payroll_amount["pension_comp"] = line.amount
            elif line.code == 'INCTAX':
                payroll_amount["tax"] = line.amount
            elif line.code == 'TDED':
                payroll_amount["total_deduction"] = line.amount
            elif line.code == 'OVERTIME':
                payroll_amount["overtime"] = line.amount
            elif line.code == 'HRA':
                payroll_amount["hra"] = line.amount
            elif line.code == 'DA':
                payroll_amount["da"] = line.amount
            elif line.code == 'Travel':
                payroll_amount["travel_allowance"] = line.amount
            elif line.code == 'NTravel':
                payroll_amount["travel_allowance_notax"] = line.amount
            elif line.code == 'MEAL':
                payroll_amount["meal_allowance"] = line.amount
            elif line.code == 'MEDICAL':
                payroll_amount["medical_allowance"] = line.amount
            elif line.code == 'COMMUNICATION':
                payroll_amount["communication_allowance"] = line.amount
            elif line.code == 'INA':
                payroll_amount["internet_allowance"] = line.amount
            elif line.code == 'FUEL':
                payroll_amount["fuel_allowance"] = line.amount
            elif line.code == 'ULP':
                payroll_amount["unused_leave_payment"] = line.amount
            elif line.code == 'SEVERANCE':
                payroll_amount["severance_pay_compensation"] = line.amount
            elif line.code == 'TRAINING':
                payroll_amount["training_development"] = line.amount
            elif line.code == 'POSITION':
                payroll_amount["position_allowance"] = line.amount
            elif line.code == 'DESALL':
                payroll_amount["desert_allowance"] = line.amount
            elif line.code == 'REPRESENTATION':
                payroll_amount["representation_allowance"] = line.amount
            elif line.code == 'EXPENSE':
                payroll_amount["expense"] = line.amount
            elif line.code == 'LOAN':
                payroll_amount["loan"] = line.amount
            elif line.code == 'ADVANCE_SALARY':
                payroll_amount["advance_salary"] = line.amount
            elif line.code == 'BONUS':
                payroll_amount["bonus"] = line.amount
            elif line.code == 'Severance net Payment':
                payroll_amount["total_payment"] = line.amount
            elif line.code == 'Severance Tax Payment':
                payroll_amount["total_adjusted_payout"] = line.amount
            elif line.code == 'EMPR':
                payroll_amount["provident_employee"] = line.amount
            elif line.code == 'EPRNT':
                payroll_amount["provident_employer"] = line.amount
        return payroll_amount

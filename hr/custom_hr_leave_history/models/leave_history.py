import datetime
from odoo import _, api, fields, models
from datetime import datetime


class CustomHrLeaveList(models.TransientModel):
    _name = "custom.hr.leave"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "custom.hr.leave"
    employee_id = fields.Many2one('hr.employee', string="Employee")
    last_year = fields.Float(string="Balance Forwarded")
    current_year_entitlement = fields.Float(string="Current year entitlement ")
    current_balance = fields.Float(string="Entitled Leave days to date", compute="compute_current_balance")
    allocated_days = fields.Float(string="Total Entitlement Balance")
    taken_days = fields.Float(string="Taken Day")
    this_year = fields.Float(string="This Year")
    total = fields.Float(string="Total Available")
    total_remaining = fields.Float(string="Total Remaining Balance", compute="compute_total_remaining")
    total_balance = fields.Float(string="Total Leave Balance to date", compute="compute_total_balance")
    total_to_date = fields.Float(string="Total Balance To Date", compute="compute_total_to_date")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date To")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

    def compute_total_remaining(self):
        for rec in self:
            rec.total_remaining=rec.total_balance-rec.taken_days


    def _get_domain(self):
        return [('employee_id.user_id', '=', self.env.user.id)]

    @api.depends('last_year', 'current_balance')
    def compute_total_balance(self):
        for rec in self:
            rec.total_balance=rec.current_balance+rec.last_year

    @api.depends('this_year')
    def compute_current_balance(self):
        for rec in self:
            current_date = datetime.now()
            current_year = current_date.year
            start_date = datetime(current_year, 7, 1)
            month_diff = 0

            if current_date < start_date:
                start_date = datetime(current_year - 1, 7, 1)

            # Calculate the difference in months
            months = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
            if rec.employee_id.contract_id:
                contract_start_date=rec.employee_id.contract_id.date_start
                contract_date_start = fields.Datetime.from_string(contract_start_date)

                if contract_date_start>start_date:
                    years_diff = contract_date_start.year - start_date.year
                    months_diff = contract_date_start.month - start_date.month
                    month_diff = (years_diff * 12) + months_diff

            months = months - month_diff
            rec.current_balance = (rec.current_year_entitlement/12)*months

    @api.depends('current_balance','last_year')
    def compute_total_to_date(self):
        for rec in self:
            rec.total_to_date = rec.current_balance + rec.last_year

    def read(self, fields=None, load='_classic_read'):
        if not self.env.context.get('refresh_report'):
            self = self.with_context(refresh_report=True)
            self.generate_leave_report()
        return super(CustomHrLeaveList, self).read(fields=fields, load=load)

    def search(self, args, offset=0, limit=None, order=None):
        if not self.env.context.get('refresh_report'):
            self = self.with_context(refresh_report=True)
            self.generate_leave_report()
        return super(CustomHrLeaveList, self).search(args, offset=offset, limit=limit, order=order)

    def generate_leave_report(self):
        self.env['custom.hr.leave'].search([]).unlink()
        current_date = datetime.now()
        current_year = datetime.now().year
        start_date = (current_year, 7, 1)
        if not current_date >= datetime(*start_date):
            start_date = (current_year - 1, 7, 1)
        allocation1 = self.calculate_allocation()
        allocations = [record for record in allocation1 if record['balance_days'] >0]
        used_leaves = [record for record in allocation1 if record['balance_days'] < 0]
        employee_ids = self.env['hr.employee'].sudo().search([('active', '=', True)])
        for employee in employee_ids:
            this_year = 0
            total_allocated = 0
            last_year = 0
            total_used = 0
            this_year_allocated = 0
            leave_type_ids=[]
            for allocation in allocations:
                if allocation['employee_id'] == employee.id and allocation['balance_days'] > 0:
                    date_from = (allocation['date_from'].year, allocation['date_from'].month, allocation['date_from'].day)
                    if start_date <= date_from:
                        this_year += allocation['balance_days']
                        this_year_allocated += allocation['allocated_days']
                    else:
                        last_year += allocation['balance_days']
                    total_allocated += allocation['allocated_days']
                    leave_type_ids.append(allocation['leave_type_id'])
                    total_used += allocation['taken_days']
            if (this_year + last_year) > 0:
                taken_all=[record for record in allocation1 if record['leave_type_id'] in leave_type_ids and record['balance_days'] < 0 and employee.id==record['employee_id']]
                total_used=0
                for t_day in taken_all:
                    total_used+=t_day['taken_days']
                leave_type_ids=False
                if total_used < last_year:
                    last_year-=total_used
                else:
                    this_year=last_year+this_year-total_used

                report_row = {
                    'employee_id': employee.id,
                    'allocated_days': total_allocated,
                    'current_year_entitlement': this_year_allocated,
                    'taken_days': total_used,
                    'this_year': this_year,
                    'last_year': last_year,
                    'total': this_year + last_year,
                }
                total_used=False
                self.env['custom.hr.leave'].sudo().create(report_row)

    # def calculate_allocation(self):
    #     leave_balance_report = []
    #     employee_ids = self.env['hr.employee'].sudo().search([('active', '=', True)])
    #     for employee_id in employee_ids:
    #         leave_allocation_ids = self.env['hr.leave.allocation'].sudo().search(
    #             [('holiday_status_id.active', '=', True), ('employee_id', '=', employee_id.id),
    #              ('state', '=', 'validate')]
    #         )
    #         leave_ids = self.env['hr.leave'].sudo().search(
    #             [('holiday_status_id.active', '=', True), ('employee_id', '=', employee_id.id),
    #              ('state', '=', 'validate')]
    #         )
    #         balances_dict = {}
    #         for allocation in leave_allocation_ids:
    #             key = (allocation.holiday_status_id.id, allocation.date_from, allocation.date_to)
    #             if key not in balances_dict:
    #                 balances_dict[key] = {
    #                     'allocated': allocation.number_of_days,
    #                     'taken': 0.0,
    #                     'date_from': allocation.date_from,
    #                     'end_date': allocation.date_to
    #                 }
    #             else:
    #                 balances_dict[key]['allocated'] += allocation.number_of_days
    #
    #         for leave in leave_ids:
    #             key = (leave.holiday_status_id.id, leave.date_from, leave.date_to)
    #             if key not in balances_dict:
    #                 balances_dict[key] = {
    #                     'allocated': 0.0,
    #                     'taken': leave.number_of_days,
    #                     'date_from': leave.date_from,
    #                     'end_date': leave.date_to
    #                 }
    #             else:
    #                 balances_dict[key]['taken'] += leave.number_of_days
    #
    #         for (leave_type, date_from, date_to), child_dict in balances_dict.items():
    #             leave_balance_report.append({
    #                 'employee_id': employee_id.id,
    #                 'leave_type_id': leave_type,
    #                 'allocated_days': child_dict['allocated'],
    #                 'taken_days': child_dict['taken'],
    #                 'balance_days': child_dict['allocated'] - child_dict['taken'],
    #                 'date_from': date_from,
    #                 'end_date': date_to
    #             })
    #
    #     return leave_balance_report

    # def calculate_allocation(self):
    #     leave_balance_report = []
    #     employee_ids = self.env['hr.employee'].sudo().search([('active', '=', True)])
    #     for employee_id in employee_ids:
    #         leave_allocation_ids = self.env['hr.leave.allocation'].sudo().search(
    #             [('holiday_status_id.active', '=', True), ('employee_id', '=', employee_id.id),
    #              ('state', '=', 'validate')])
    #         leave_ids = self.env['hr.leave'].sudo().search(
    #             [('holiday_status_id.active', '=', True), ('employee_id', '=', employee_id.id),
    #              ('state', '=', 'validate')])
    #         balances_dict = {}
    #         for allocation in leave_allocation_ids:
    #             if allocation.holiday_status_id.id not in balances_dict:
    #                 balances_dict[allocation.holiday_status_id.id] = {
    #                     'allocated': allocation.number_of_days,
    #                     'taken': 0.0,
    #                     'date_from': allocation.date_from,
    #                     'end_date': allocation.date_to
    #                 }
    #             else:
    #                 balances_dict[allocation.holiday_status_id.id]['allocated'] += allocation.number_of_days
    #         for leave in leave_ids:
    #             if leave.holiday_status_id.id not in balances_dict:
    #                 balances_dict[leave.holiday_status_id.id] = {
    #                     'allocated': 0.0,
    #                     'taken': leave.number_of_days,
    #                     'date_from': None,
    #                     'end_date': None
    #                 }
    #             else:
    #                 balances_dict[leave.holiday_status_id.id]['taken'] += leave.number_of_days
    #
    #         for leave_type, child_dict in balances_dict.items():
    #             leave_balance_report.append({
    #                 'employee_id': employee_id.id,
    #                 'leave_type_id': leave_type,
    #                 'allocated_days': child_dict['allocated'],
    #                 'taken_days': child_dict['taken'],
    #                 'balance_days': child_dict['allocated'] - child_dict['taken'],
    #                 'date_from': child_dict['date_from'],
    #                 'end_date': child_dict['end_date']
    #             })
    #     return leave_balance_report

    def calculate_allocation(self):
        leave_balance_report = []
        employee_ids = self.env['hr.employee'].sudo().search([('active', '=', True)])
        for employee_id in employee_ids:
            leave_allocation_ids = self.env['hr.leave.allocation'].sudo().search(
                [('holiday_status_id.active', '=', True), ('employee_id', '=', employee_id.id),
                 ('state', '=', 'validate')])
            leave_ids = self.env['hr.leave'].sudo().search(
                [('holiday_status_id.active', '=', True), ('employee_id', '=', employee_id.id),
                 ('state', '=', 'validate')])

            # Dictionary to store balances grouped by both leave type and allocation
            balances_dict = {}

            for allocation in leave_allocation_ids:
                key = (allocation.holiday_status_id.id, allocation.id)
                if key not in balances_dict:
                    balances_dict[key] = {
                        'allocated': allocation.number_of_days,
                        'taken': 0.0,
                        'date_from': allocation.date_from,
                        'end_date': allocation.date_to
                    }
                else:
                    balances_dict[key]['allocated'] += allocation.number_of_days

            for leave in leave_ids:
                key = (leave.holiday_status_id.id, leave.holiday_allocation_id.id)
                if key not in balances_dict:
                    balances_dict[key] = {
                        'allocated': 0.0,
                        'taken': leave.number_of_days,
                        'date_from': None,
                        'end_date': None
                    }
                else:
                    balances_dict[key]['taken'] += leave.number_of_days

            for (leave_type, allocation_id), child_dict in balances_dict.items():
                leave_balance_report.append({
                    'employee_id': employee_id.id,
                    'leave_type_id': leave_type,
                    'allocation_id': allocation_id,  # Include allocation ID in the report
                    'allocated_days': child_dict['allocated'],
                    'taken_days': child_dict['taken'],
                    'balance_days': child_dict['allocated'] - child_dict['taken'],
                    'date_from': child_dict['date_from'],
                    'end_date': child_dict['end_date']
                })

        return leave_balance_report


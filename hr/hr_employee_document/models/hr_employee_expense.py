# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class HRInstitution(models.Model):
    _name = 'hr.institutions'
    _description = 'HR Language'

    name = fields.Char(string='Institution', required=True)



class HRLanguage(models.Model):
    _name = 'hr.language'
    _description = 'HR Language'

    name = fields.Char(string='Language', required=True)


class HRUnit(models.Model):
    _name = 'hr.unit'
    _description = 'HR business unit'
    _rec_name = 'unit'

    
    unit = fields.Char(string='Unit')



class EmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    filter_for_expense = fields.Boolean(store=False, search='_search_filter_for_expense')

    def _search_filter_for_expense(self, operator, value):
        assert operator == '=' and value, "Operation not supported"

        res = [('id', '=', 0)]  # Nothing accepted by domain, by default
        user = self.env.user
        employee = user.employee_id
        if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups(
                'account.group_account_user'):
            res = ['|', ('company_id', '=', False),
                   ('company_id', 'child_of', self.env.company.root_id.id)]  # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_team_approver') and user.employee_ids:
            res = [
                '|', '|', '|',
                ('department_id.manager_id', '=', employee.id),
                ('parent_id', '=', employee.id),
                ('id', '=', employee.id),
                ('expense_manager_ids', 'in', [user.id]),
                '|', ('company_id', '=', False), ('company_id', '=', employee.company_id.id),
            ]
        elif user.employee_id:
            res = [('id', '=', employee.id), '|', ('company_id', '=', False),
                   ('company_id', '=', employee.company_id.id)]
        return res

class Employee(models.Model):
    _inherit = 'hr.employee'

    resume_attachment = fields.Binary("Resume", attachment=True)
    resume_filename = fields.Char("Filename")
    staff_card_no = fields.Char(string="Staf Card No")
    tin_no = fields.Char(string="Tin No")
    pension_no = fields.Char(string="Pension No")
    pin = fields.Char(string="Badge Id")
    # barcode = fields.Char(string="Badge Id",compute="_compute_badge")
    language = fields.Many2many(
        'hr.language',  # Related model
        string='Languages',
        groups="hr.group_hr_user"
    )
    unit = fields.Char(string="Unit")
    
    unit_id = fields.Many2one('hr.unit',string="Unit")

    institutions = fields.Many2many('hr.institutions', string="Institutions",groups="hr.group_hr_user")
    membership_documents = fields.Many2many(
        'ir.attachment',  # Link to the attachment model
        string='Membership Documents',
        help='Upload multiple documents related to membership.',
         # Visible only if ssnid has a value
    )

    country_of_birth = fields.Many2one(
        'res.country',  # Link to the res.country model
        string='Country of Birth',
        compute='_compute_country_of_birth',
        store=True,  # Store the value in the database for faster access
    )
    identification_id = fields.Char(string="Identification No", compute="_compute_id_no")
    barcode = fields.Char(string="Staff Id", compute="_compute_badge_no")

    @api.depends('staff_card_no')
    def _compute_badge_no(self):
        for employee in self:
            employee.barcode = employee.staff_card_no

    @api.depends('pin')
    def _compute_id_no(self):
        for employee in self:
            employee.identification_id = employee.pin

    @api.depends('private_country_id')
    def _compute_country_of_birth(self):
        """
        Compute the country_of_birth field based on private_country_id.
        """
        for employee in self:
            employee.country_of_birth = employee.private_country_id


    def _compute_badge(self):
        for rec in self:
            rec.pin = rec.staff_card_no

    leave_manager_ids = fields.Many2many(
        'res.users',
        string='Leave Managers',
        relation='hr_employee_leave_manager_rel',  # Custom relation table
        column1='hr_employee_id',  # Column for the current record (hr.employee)
        column2='res_users_id',  # Column for the related record (res.users)
        help="Select the users responsible for approving leave requests for this employee.",
        groups="hr_holidays.group_hr_holidays_user",
    )

    attendance_manager_ids = fields.Many2many(
        'res.users',
        string='Attendance Managers',
        store=True,
        readonly=False,
        domain="[('share', '=', False), ('company_ids', 'in', company_id)]",
        groups="hr_attendance.group_hr_attendance_manager",
        help="The users set in Attendance will access the attendance of the employee through the dedicated app and will be able to edit them."
    )

    def _get_user_m2o_to_empty_on_archived_employees(self):
        return super()._get_user_m2o_to_empty_on_archived_employees() + ['leave_manager_ids']

    def _group_hr_expense_user_domain(self):
        group = self.env.ref('hr_expense.group_hr_expense_team_approver', raise_if_not_found=False)
        return [('groups_id', 'in', group.ids)] if group else []

    expense_manager_ids = fields.Many2many(
        'res.users',
        string='Expense Managers',
        relation='hr_employee_expense_manager_rel',  # Custom relation table
        column1='hr_employee_id',  # Column for the current record (hr.employee)
        column2='res_users_id',  # Column for the related record (res.users)
        help="Select the users responsible for approving expenses for this employee.",
        groups="hr_expense.group_hr_expense_manager",
    )

    @api.model_create_multi
    def create(self, vals_list):
        officer_group = self.env.ref('hr_attendance.group_hr_attendance_officer', raise_if_not_found=False)
        group_updates = []
        for vals in vals_list:
            if officer_group and vals.get('attendance_manager_ids'):
                group_updates.extend((4, user_id) for user_id in vals['attendance_manager_ids'][0][2])
        if group_updates:
            officer_group.sudo().write({'users': group_updates})
        return super().create(vals_list)

    def write(self, values):
        old_officers = self.env['res.users']
        if 'attendance_manager_ids' in values:
            # Handle the case where attendance_manager_ids is empty or not properly formatted
            if values['attendance_manager_ids'] and isinstance(values['attendance_manager_ids'], list):
                # Extract the list of user IDs from the Many2many command
                if values['attendance_manager_ids'][0][0] == 6:  # Check if it's a replace command
                    new_officer_ids = values['attendance_manager_ids'][0][2]
                    new_officers = self.env['res.users'].browse(new_officer_ids)
                else:
                    # Handle other cases (e.g., add, remove)
                    new_officers = self.env['res.users']
            else:
                # If attendance_manager_ids is empty or invalid, set new_officers to an empty recordset
                new_officers = self.env['res.users']

            # Add new officers to the group
            officers_group = self.env.ref('hr_attendance.group_hr_attendance_officer', raise_if_not_found=False)
            if officers_group:
                for officer in new_officers:
                    if not officer.has_group('hr_attendance.group_hr_attendance_officer'):
                        officer.sudo().write({'groups_id': [(4, officers_group.id)]})

        res = super(Employee, self).write(values)
        old_officers.sudo()._clean_attendance_officers()
        return res
    @api.depends('parent_id')
    def _compute_expense_managers(self):
        for employee in self:
            previous_manager = employee._origin.parent_id.user_id
            manager = employee.parent_id.user_id
            if manager and manager.has_group('hr_expense.group_hr_expense_user') \
                    and (manager in employee.expense_manager_ids or not employee.expense_manager_ids):
                employee.expense_manager_ids = [(4, manager.id)]
            elif not employee.expense_manager_ids:
                employee.expense_manager_ids = [(5, 0, 0)]

    def _get_user_m2o_to_empty_on_archived_employees(self):
        return super()._get_user_m2o_to_empty_on_archived_employees() + ['expense_manager_ids']


class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    expense_manager_ids = fields.Many2many('res.users', readonly=True)


class User(models.Model):
    _inherit = ['res.users']

    expense_manager_ids = fields.Many2many(related='employee_id.expense_manager_ids', readonly=False)

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['expense_manager_ids']
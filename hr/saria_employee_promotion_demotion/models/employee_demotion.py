from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    demotion_ids = fields.One2many('employee.demotion', 'employee_id', string='Demotion')
    old_job_id = fields.Many2one('hr.job', related='contract_id.job_id', string='Previous Job Position', readonly=True)
    old_wage = fields.Float('Previous Salary', readonly=True,compute='_compute_current_job_id')
    current_job_id = fields.Many2one('hr.job', string='Current Job Position', compute='_compute_current_job_id', store=True)
    current_wage = fields.Float('Current Salary', compute='_compute_current_wage', store=True)


    @api.depends('contract_ids', 'contract_ids.job_id', 'contract_ids.wage')
    def _compute_current_job_id(self):
        for employee in self:
            contract = employee.contract_ids.sorted(key=lambda r: r.date_start, reverse=True)[:1]
            employee.current_job_id = contract.job_id if contract else False

    @api.depends('employee_id')
    def _compute_old_wage(self):
        for demotion in self:
            if demotion.employee_id:
                contract = self.env['hr.contract'].search([('employee_id', '=', demotion.employee_id.id)], limit=1,
                                                          order='date_start desc')
                demotion.old_wage = contract.wage if contract else 0.0

    @api.depends('contract_ids', 'contract_ids.job_id', 'contract_ids.wage')
    def _compute_current_wage(self):
        for employee in self:
            contract = employee.contract_ids.sorted(key=lambda r: r.date_start, reverse=True)[:1]
            employee.current_wage = contract.wage if contract else 0.0


class EmployeeDemotion(models.Model):
    _name = 'employee.demotion'
    _description = 'Employee Demotion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    old_job = fields.Char('previous job position',  readonly=True)
    old_job_id = fields.Many2one('hr.job', string='Previous Job Position',)
    old_salary = fields.Float('Previous Salary')
    demotion_date = fields.Date('Demotion Date', default=fields.Date.today())
    # demotion_type = fields.Selection([
    #     ('normal', 'Normal'),
    #     ('special', 'Special'),
    # ], string='Demotion Type', default='normal')
    new_job = fields.Many2one('hr.job', string='New Job Position')
    new_job_id = fields.Many2one('hr.job', string='New Job Position')
    new_wage = fields.Float('New Salary')
    old_hra = fields.Float('HRA')
    old_da = fields.Float('DA')
    old_travel_allowance = fields.Float('Travel Allowance')
    old_meal_allowance = fields.Float('Meal Allowance')
    old_medical_allowance = fields.Float('Medical Allowance')
    old_other_allowance = fields.Float('Other Allowance')
    old_inflation_adjustment = fields.Float('Inflation Adjustment')
    old_communication_allowance = fields.Float('Communication Allowance')
    old_internet_allowance = fields.Float('Internet Allowance')
    old_fuel_allowance = fields.Float('Fuel Allowance')
    old_unused_leave_payment = fields.Float('Unused Leave Payment')
    old_severance_pay_compensation = fields.Float('Severance Pay Compensation')
    old_training_development = fields.Float('Training Development')
    old_position_allowance = fields.Float('Position Allowance')
    old_desert_allowance = fields.Float('Desert Allowance')
    old_representation_allowance = fields.Float('Representation Allowance')
    old_transportation_allowance= fields.Float('Transportation Allowance')

    new_hra = fields.Float('HRA')
    new_da = fields.Float('DA')
    new_travel_allowance = fields.Float('Travel Allowance')
    new_meal_allowance = fields.Float('Meal Allowance')
    new_medical_allowance = fields.Float('Medical Allowance')
    new_other_allowance = fields.Float('Other Allowance')
    new_inflation_adjustment = fields.Float('Inflation Adjustment')
    new_communication_allowance = fields.Float('Communication Allowance')
    new_internet_allowance = fields.Float('Internet Allowance')
    new_fuel_allowance = fields.Float('Fuel Allowance')
    new_unused_leave_payment = fields.Float('Unused Leave Payment')
    new_severance_pay_compensation = fields.Float('Severance Pay Compensation')
    new_training_development = fields.Float('Training Development')
    new_position_allowance = fields.Float('Position Allowance')
    new_desert_allowance = fields.Float('Desert Allowance')
    new_representation_allowance = fields.Float('Representation Allowance')
    new_transportation_allowance = fields.Float('Transportation Allowance')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved')],
        default="draft")

    def action_submit(self):
        self.state = 'submit'

    @api.model
    def create(self, vals):
        employee_id = vals['employee_id']
        contract = self.env['hr.contract'].search(
            ['&', ('employee_id', '=', employee_id), ('state', '=', 'open')])
        record = super(EmployeeDemotion, self).create(vals)

        if contract:
            record.old_salary = contract.wage
            record.old_salary = contract.wage
            record.old_hra = contract.hra
            record.old_da = contract.da
            if contract.job_id:
                record.old_job = contract.job_id.name
                record.old_job_id = contract.job_id.id
            record.old_travel_allowance = contract.travel_allowance
            record.old_meal_allowance = contract.meal_allowance
            record.old_other_allowance = contract.other_allowance
            record.old_other_allowance = contract.other_allowance
            record.old_inflation_adjustment = contract.inflation_adjustment
            record.old_communication_allowance = contract.communication_allowance
            record.old_internet_allowance = contract.internet_allowance
            record.old_fuel_allowance = contract.fuel_allowance
            record.old_unused_leave_payment = contract.unused_leave_payment
            record.old_severance_pay_compensation = contract.severance_pay_compensation
            record.old_training_development = contract.training_development
            record.old_position_allowance = contract.position_allowance
            record.old_desert_allowance = contract.desert_allowance
            record.old_representation_allowance = contract.representation_allowance
            record.old_transportation_allowance = contract.transportation_allowance

        return  record

    @api.onchange('employee_id')
    def _compute_old_salary(self):
        for employee in self:
            contract = self.env['hr.contract'].search(
                ['&', ('employee_id', '=', employee.employee_id.id), ('state', '=', 'open')])
            if contract:
                employee.old_salary = contract.wage
                employee.old_hra = contract.hra
                employee.old_da = contract.da
                if contract.job_id:
                    employee.old_job = contract.job_id.name
                    employee.old_job_id = contract.job_id.id

                employee.old_travel_allowance = contract.travel_allowance
                employee.old_meal_allowance = contract.meal_allowance
                employee.old_other_allowance = contract.other_allowance
                employee.old_other_allowance = contract.other_allowance
                employee.old_inflation_adjustment = contract.inflation_adjustment
                employee.old_communication_allowance = contract.communication_allowance
                employee.old_internet_allowance = contract.internet_allowance
                employee.old_fuel_allowance = contract.fuel_allowance
                employee.old_unused_leave_payment = contract.unused_leave_payment
                employee.old_severance_pay_compensation = contract.severance_pay_compensation
                employee.old_training_development = contract.training_development
                employee.old_position_allowance = contract.position_allowance
                employee.old_desert_allowance = contract.desert_allowance
                employee.old_representation_allowance = contract.representation_allowance
                employee.old_transportation_allowance = contract.transportation_allowance
            else:
                employee.old_salary = 0.0

    # @api.depends('employee_id')
    # def _compute_old_wage(self):
    #     for promotion in self:
    #         if promotion.employee_id:
    #             contract = self.env['hr.contract'].search([('employee_id', '=', promotion.employee_id.id)], limit=1, order='date_start desc')
    #             promotion.old_wage = contract.wage if contract else 0.0

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], limit=1, order='date_start desc')
            self.old_job_id = contract.job_id.id if contract else False

    @api.model
    def _update_employee_job_salary(self, demotion):
        # if demotion.new_job and demotion.new_wage:
            update = self.env['hr.contract'].search(
                ['&', ('employee_id', '=', demotion.employee_id.id), ('state', '=', 'open')])
            update.write({
                'job_id': demotion.new_job.id,
                'wage': demotion.new_wage,
                'hra' : demotion.new_hra,
                'da': demotion.new_da,
                'travel_allowance': demotion.new_travel_allowance,
                'meal_allowance': demotion.new_meal_allowance,
                'other_allowance': demotion.new_other_allowance,
                'inflation_adjustment': demotion.new_inflation_adjustment,
                'communication_allowance': demotion.new_communication_allowance,
                'internet_allowance': demotion.new_internet_allowance,
                'fuel_allowance': demotion.new_fuel_allowance,
                'unused_leave_payment': demotion.new_unused_leave_payment,
                'severance_pay_compensation': demotion.new_severance_pay_compensation,
                'training_development': demotion.new_training_development,
                'position_allowance': demotion.new_position_allowance,
                'desert_allowance': demotion.new_desert_allowance,
                'representation_allowance': demotion.new_representation_allowance,
                'transportation_allowance': demotion.new_transportation_allowance
            })

    # def action_validate_promotion(self):
    #     for demotion in self:
    #         demotion._update_employee_job_salary(demotion)

    def action_approve(self):
        for demotion in self:
            self.state = 'approve'
            demotion._update_employee_job_salary(demotion)





from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    promotion_ids = fields.One2many('employee.promotion', 'employee_id', string='Promotions')
    old_job_id = fields.Many2one('hr.job', string='Previous Job Position', readonly=True)
    old_wage = fields.Float('Previous Salary', readonly=True)
    current_job_id = fields.Many2one('hr.job', string='Current Job Position', compute='_compute_current_job_id', store=True)
    current_wage = fields.Float('Current Salary', compute='_compute_current_wage', store=True)

    @api.depends('contract_ids', 'contract_ids.job_id', 'contract_ids.wage')
    def _compute_current_job_id(self):
        for employee in self:
            contract = employee.contract_ids.sorted(key=lambda r: r.date_start, reverse=True)[:1]
            employee.current_job_id = contract.job_id if contract else False



    # @api.depends('employee_id')
    # def _compute_old_wage(self):
    #     for promotion in self:
    #         if promotion.employee_id:
    #             contract = self.env['hr.contract'].search([('employee_id', '=', promotion.employee_id.id)], limit=1,
    #                                                       order='date_start desc')
    #             promotion.old_wage = contract.wage if contract else 0.0

    @api.depends('contract_ids', 'contract_ids.job_id', 'contract_ids.wage')
    def _compute_current_wage(self):
        for employee in self:
            contract = employee.contract_ids.sorted(key=lambda r: r.date_start, reverse=True)[:1]
            employee.current_wage = contract.wage if contract else 0.0


class EmployeePromotion(models.Model):
    _name = 'employee.promotion'
    _description = 'Employee Promotion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    Type = fields.Selection(
        selection=[
            ('promotion', "Promotion"),
            ('amendment', "Amendment"),
        ],
        string="Type",
        default='promotion')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    old_currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    old_designation = fields.Char('previous job position')
    old_job_id = fields.Many2one('hr.job', string='Previous Job Position')
    old_wage = fields.Float('Previous Salary')
    promotion_date = fields.Date('Promotion Date', default=fields.Date.today())
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
    old_transportation_allowance = fields.Float('Transportation Allowance')

    new_currency_id = fields.Many2one('res.currency', string='Currency', required=True)
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
        ('draft','Draft'),
        ('submit', 'Submitted'),
        ('approve','Approved')],
        default="draft")
    # promotion_type = fields.Selection([
    #     ('normal', 'Normal'),
    #     ('fast-track', ''),
    #     ('special', 'Special'),
    # ], string='Promotion Type', default='normal')
    # new_designation = fields.Many2one('hr.job', string='New Job Position')
    new_job_id = fields.Many2one('hr.job', string='New Job Position')
    new_salary = fields.Float('New Salary')

    @api.model
    def create(self, vals):
        employee_id=vals['employee_id']
        contract = self.env['hr.contract'].search(
            ['&', ('employee_id', '=', employee_id), ('state', '=', 'open')])
        record = super(EmployeePromotion, self).create(vals)
        if contract:
            record.old_currency_id = contract.currency_id
            record.old_wage = contract.wage
            record.old_hra = contract.hra
            record.old_da = contract.da
            record.old_job_id = contract.job_id.id
            record.old_designation = contract.job_id.name
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

        return record


    def action_submit(self):
        self.state = 'submit'



    @api.onchange('employee_id')
    def _compute_old_salary(self):
        for employee in self:
            contract = self.env['hr.contract'].search([('employee_id', '=', employee.employee_id.id), ('state', '=', 'open')])
            if contract:
                employee.new_currency_id = contract.currency_id
                employee.old_currency_id = contract.currency_id
                employee.old_wage = contract.wage
                employee.old_hra = contract.hra
                employee.old_da = contract.da
                employee.old_job_id = contract.job_id.id
                employee.old_designation = contract.job_id.name
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
                employee.old_wage = 0.0

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
    def _update_employee_job_salary(self, promotion):
            update = self.env['hr.contract'].search(
                ['&',('employee_id', '=', promotion.employee_id.id), ('state', '=', 'open')])
            update.write({
                'currency_id': promotion.new_currency_id.id,
                'job_id': promotion.new_job_id.id,
                'wage': promotion.new_salary,
                'hra' : promotion.new_hra,
                'da': promotion.new_da,
                'travel_allowance': promotion.new_travel_allowance,
                'meal_allowance': promotion.new_meal_allowance,
                'other_allowance': promotion.new_other_allowance,
                'inflation_adjustment': promotion.new_inflation_adjustment,
                'communication_allowance': promotion.new_communication_allowance,
                'internet_allowance': promotion.new_internet_allowance,
                'fuel_allowance': promotion.new_fuel_allowance,
                'unused_leave_payment': promotion.new_unused_leave_payment,
                'severance_pay_compensation': promotion.new_severance_pay_compensation,
                'training_development': promotion.new_training_development,
                'position_allowance': promotion.new_position_allowance,
                'desert_allowance': promotion.new_desert_allowance,
                'representation_allowance': promotion.new_representation_allowance,
                'transportation_allowance': promotion.new_transportation_allowance


            })

    def action_approve(self):
      for promotion in self:
        self.state = 'approve'
        promotion._update_employee_job_salary(promotion)

    # def action_validate_promotion(self):
    #     for promotion in self:
    #         self.state = 'approve'
    #         promotion._update_employee_job_salary(promotion)
    #
    # def action_approve(self):
    #     self.state = 'approve'




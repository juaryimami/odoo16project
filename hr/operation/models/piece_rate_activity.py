from odoo import models, fields, api, _


class PieceRateActivity(models.Model):
    _name = 'piece.rate.activity'
    _description = 'Piece Rate Activity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name',required=True)
    description=fields.Text(string="Description")



class PieceRateActivityRate(models.Model):
    _name = 'piece.rate.activity.rate'
    _description = 'Piece Rate Activity Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'activity_id'

    project_id = fields.Many2one('agent.project', ondelete='cascade', string='Project', required=True)
    # calculate_profit_margin = fields.Char(related="project_id.calculate_profit_margin")
    calculate_profit_margin = fields.Selection([
        ('employee_cost', 'Employee Cost'),
        ('basic_salary', 'Basic Salary'),
        ('given_employee_cost', 'Given Employee Cost'),
    ], string='Calculate Admin and  Profit Margin From', related="project_id.calculate_profit_margin",
        defualt='employee_cost')
    service_id = fields.Many2one('product.product', domain=[('detailed_type','=','service'),('sale_ok','=',True)], string='Service')
    region_id = fields.Many2one('tax.region', ondelete='cascade', string='Region')
    location_id = fields.Many2one('agent.location', ondelete='cascade', string='Location')
    activity_id = fields.Many2one('piece.rate.activity',string="Activity",required=True)
    uom_id = fields.Many2one('piece.rate.uom',string="UOM",required=True)
    edomias_rate = fields.Float(string='Monthly Payment', compute="compute_edomias_rate", required=True)
    employee_rate = fields.Float(string='Basic Salary',required=True)
    admin_cost = fields.Float(string="Administration Cost")
    profit_margin = fields.Float(string="Profit Margin")

    # New allowance fields
    hra = fields.Float(string='Housing Allowance', default=0.0)
    hra_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')
    da = fields.Float(string='Position Allowance', default=0.0)
    da_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')
    travel_allowance = fields.Float(string='Transport Allowance', default=0.0)
    travel_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    project_transport_allowance = fields.Float(string='Projects Transport Allowance', default=0.0)
    project_transport_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    project_coordination_allowance = fields.Float(string='Projects Coordination Allowance', default=0.0)
    project_coordination_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    provision_for_severance_pay = fields.Float(string='Provision for severance pay', default=0.0)
    provision_for_severance_pay_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    meal_allowance = fields.Float(string='Meal Allowance', default=0.0)
    meal_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')
    medical_allowance = fields.Float(string='Medical Insurance', default=0.0)
    medical_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')
    accident_allowance = fields.Float(string='Accident Insurance', default=0.0)
    accident_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')
    uniform_allowance = fields.Float(string='Uniform', default=0.0)
    uniform_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')
    desert_allowance = fields.Float(string='Desert Allowance', compute='compute_desert_allowance', default=0.0)
    desert_allowance_rate = fields.Many2one('operation.desert.allowance', string='Desert Allowance Rate')
    other_allowance = fields.Float(string='Other Allowance', default=0.0)
    other_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    communication_allowance = fields.Float(string='Communication Allowance', default=0.0)
    communication_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    additional_duty_allowance = fields.Float(string='Additional Duty Allowance', default=0.0)
    additional_duty_allowance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    employee_cost = fields.Float(compute='_compute_employee_cost', string='Employee Cost')
    employee_cost1 = fields.Float(string='Employee Cost')
    provident_fund = fields.Float(compute='_compute_provident_fund', string='Provident Fund(11%)')

    pension_rate = fields.Float(string="Pension Contribution")
    pension_rate_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    fidelity_insurance = fields.Float(string="Fidelity Insurance")
    fidelity_insurance_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    provision_for_leave = fields.Float(string="Provision For Leave")
    provision_for_leave_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    material_cost = fields.Float(string="Material Cost")
    material_cost_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')




    @api.depends('desert_allowance_rate')
    def compute_desert_allowance(self):
        for rec in self:
            if rec.desert_allowance_rate:
                rec.desert_allowance = (rec.desert_allowance_rate.rate * rec.employee_rate) / 100
            else:
                rec.desert_allowance = 0

    @api.depends('employee_rate', 'employee_cost', 'project_id.calculate_profit_margin',
                  'project_id.profit_margin_type')
    def compute_edomias_rate(self):
        for rec in self:
            if rec.project_id.profit_margin_type == "percentage":
                if rec.project_id.calculate_profit_margin == "basic_salary":
                    rec.edomias_rate = rec.employee_cost + rec.employee_rate * (
                                rec.project_id.profit_margin_percentage + rec.project_id.admin_cost) / 100
                else:
                    rec.edomias_rate = rec.employee_cost + (rec.employee_cost * (
                            rec.project_id.profit_margin_percentage + rec.project_id.admin_cost) / 100)
            else:
                if rec.project_id.calculate_profit_margin == "basic_salary":
                    rec.edomias_rate = rec.employee_cost + rec.project_id.profit_margin_percentage + rec.project_id.admin_cost
                else:
                    rec.edomias_rate = rec.employee_cost + rec.project_id.profit_margin_percentage + rec.project_id.admin_cost


    @api.depends('employee_rate','employee_cost1','pension_rate', 'hra', 'hra_type', 'da', 'da_type', 'travel_allowance', 'travel_allowance_type',
                 'medical_allowance', 'medical_allowance_type', 'accident_allowance', 'uniform_allowance_type',
                 'uniform_allowance', 'other_allowance', 'other_allowance_type','fidelity_insurance','provision_for_leave','material_cost')
    def _compute_employee_cost(self):
        for rec in self:
            employee_cost = 0
            if rec.project_id.calculate_profit_margin=="given_employee_cost":
                employee_cost=rec.employee_cost1
            else:
                employee_cost += rec.employee_rate
                if rec.hra_type == "percentage":
                    employee_cost += rec.employee_rate * rec.hra / 100
                else:
                    employee_cost += rec.hra
                if rec.da_type == "percentage":
                    employee_cost += rec.employee_rate * rec.da / 100
                else:
                    employee_cost += rec.da
                if rec.travel_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.travel_allowance / 100
                else:
                    employee_cost += rec.travel_allowance
                if rec.medical_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.medical_allowance / 100
                else:
                    employee_cost += rec.medical_allowance

                if rec.meal_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.meal_allowance / 100
                else:
                    employee_cost += rec.meal_allowance

                if rec.accident_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.accident_allowance / 100
                else:
                    employee_cost += rec.accident_allowance
                if rec.uniform_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.uniform_allowance / 100
                else:
                    employee_cost += rec.uniform_allowance
                if rec.other_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.other_allowance / 100
                else:
                    employee_cost += rec.other_allowance

                if rec.project_transport_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.project_transport_allowance / 100
                else:
                    employee_cost += rec.project_transport_allowance
                if rec.project_coordination_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.project_coordination_allowance / 100
                else:
                    employee_cost += rec.project_coordination_allowance

                if rec.provision_for_severance_pay_type == "percentage":
                    employee_cost += rec.employee_rate * rec.provision_for_severance_pay / 100
                else:
                    employee_cost += rec.provision_for_severance_pay
                if rec.communication_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.communication_allowance / 100
                else:
                    employee_cost += rec.communication_allowance

                if rec.additional_duty_allowance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.additional_duty_allowance / 100
                else:
                    employee_cost += rec.additional_duty_allowance
                if rec.pension_rate_type == "percentage":
                    employee_cost += rec.employee_rate * rec.pension_rate / 100
                else:
                    employee_cost += rec.pension_rate
                if rec.material_cost_type == "percentage":
                    employee_cost += rec.employee_rate * rec.material_cost / 100
                else:
                    employee_cost += rec.material_cost
                if rec.provision_for_leave_type == "percentage":
                    employee_cost += rec.employee_rate * rec.provision_for_leave / 100
                else:
                    employee_cost += rec.provision_for_leave
                if rec.fidelity_insurance_type == "percentage":
                    employee_cost += rec.employee_rate * rec.fidelity_insurance / 100
                else:
                    employee_cost += rec.fidelity_insurance
                employee_cost += rec.desert_allowance
            rec.edomias_rate = employee_cost + employee_cost * (
                    rec.project_id.profit_margin_percentage + rec.project_id.admin_cost) / 100
            rec.employee_cost = employee_cost

    @api.depends('employee_rate')
    def _compute_provident_fund(self):
        for rec in self:
            rec.provident_fund =0 # rec.employee_rate * 0.11


    def return_line_form(self):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Activities',
                'res_model': 'piece.rate.activity.rate',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_project_id': self.project_id.id,
                }
            }

    def return_line_detail(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Activities',
                'res_model': 'piece.rate.activity.rate',
                'view_mode': 'form',
                'target': 'new',
                'res_id': rec.id,
            }


class PieceRateUom(models.Model):
    _name = 'piece.rate.uom'
    _description = 'Piece Rate Uom'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name',required=True)
    description=fields.Text(string="Description")

class OtRateList(models.Model):
    _name = 'ot.rate.list'
    _description = 'OT Rate List'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'rec_name'

    name = fields.Selection([
        ('normal', 'Normal Working Day'),
        ('weekend', 'Weekend'),
        ('holiday', 'Holiday'),
        ('rest_day', 'Rest Day'),
    ], string="Working Day Type", required=True, default='normal')
    rate=fields.Float(string="Rate",required=True, default=1)
    description=fields.Text(string="Description")

    rec_name=fields.Char(compute="compute_rec_name")

    def compute_rec_name(self):
        for rec in self:
            rec.rec_name= f"{rec.name} ({rec.rate})"



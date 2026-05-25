from email.policy import default

from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    inflation_adjustment = fields.Float(string='Inflation Adjustment (Allowance)%')
    communication_allowance = fields.Float(string='Communication Allowance')
    internet_allowance = fields.Float(string='Phone and Internet Allowance')
    fuel_allowance = fields.Float(string='Fuel Allowance')
    unused_leave_payment = fields.Float(string='Unused Leave Payment')
    severance_pay_compensation = fields.Float(string='Severance Pay and Compensation')
    training_development = fields.Float(string='Training and Development')
    position_allowance = fields.Float(string='Position Allowance', compute='_compute_position_allowance', inverse='_set_position_allowance', store=True)
    desert_allowance = fields.Float(string='Desert Allowance', compute='_compute_desert_allowance', inverse='_set_desert_allowance', store=True)
    representation_allowance = fields.Float(string='Representation Allowance', compute='_compute_representation_allowance', inverse='_set_representation_allowance', store=True)

    position_allowance_percentage = fields.Float(string=' Professional Allowance')
    desert_allowance_percentage = fields.Float(string='Desert Allowance (%)')
    representation_allowance_percentage = fields.Float(string='Representation Allowance (%)')
    acting_allowance = fields.Float(string='Acting Allowance/Position Allowance (%)',   digits=(12, 4))
    transportation_allowance = fields.Float(string=' Transportation Allowance')
    daily_subsistence_allowance = fields.Float(string='Daily Subsistance Allowance')

    @api.depends('wage', 'position_allowance_percentage')
    def _compute_position_allowance(self):
        for contract in self:
            if contract.wage and contract.position_allowance_percentage:
                contract.position_allowance = contract.wage * (contract.position_allowance_percentage / 100)
            else:
                contract.position_allowance = 0.0

    def _set_position_allowance(self):
        for contract in self:
            if contract.wage:
                contract.position_allowance_percentage = (contract.position_allowance / contract.wage) * 100 if contract.position_allowance else 0.0

    @api.depends('wage', 'desert_allowance_percentage')
    def _compute_desert_allowance(self):
        for contract in self:
            if contract.wage and contract.desert_allowance_percentage:
                contract.desert_allowance = contract.wage * (contract.desert_allowance_percentage / 100)
            else:
                contract.desert_allowance = 0.0

    def _set_desert_allowance(self):
        for contract in self:
            if contract.wage:
                contract.desert_allowance_percentage = (contract.desert_allowance / contract.wage) * 100 if contract.desert_allowance else 0.0

    @api.depends('wage', 'representation_allowance_percentage')
    def _compute_representation_allowance(self):
        for contract in self:
            if contract.wage and contract.representation_allowance_percentage:
                contract.representation_allowance = contract.wage * (contract.representation_allowance_percentage / 100)
            else:
                contract.representation_allowance = 0.0

    def _set_representation_allowance(self):
        for contract in self:
            if contract.wage:
                contract.representation_allowance_percentage = (contract.representation_allowance / contract.wage) * 100 if contract.representation_allowance else 0.0

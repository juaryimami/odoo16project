# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import fields, models

class HrContract(models.Model):
    _inherit = 'hr.contract'

    transport_allowance = fields.Float(string="Transport Allowance (Cash)", tracking=True)
    housing_allowance = fields.Float(string="Housing Allowance (Cash)", tracking=True)
    position_allowance = fields.Float(string="Position Allowance (Cash)", tracking=True)
    mobile_allowance = fields.Float(string="Mobile Allowance (Cash)", tracking=True)
    meal_allowance = fields.Float(string="Meal Allowance (Cash)", tracking=True)
    desert_allowance = fields.Float(string="Desert/Hardship Allowance", tracking=True)
    
    # Exemption Toggles
    subject_to_pension = fields.Boolean(
        string="Subject to Statutory Pension", 
        default=True,
        help="If False, the 7% employee and 11% employer pension rules will be bypassed.",
        tracking=True
    )
    is_exempt_canteen_eligible = fields.Boolean(
        string="Universal Canteen Exemption", 
        help="If True, the meal allowance is 100% tax-exempt per Article 54.",
        tracking=True
    )
    travels_for_work = fields.Boolean(
        string="Travels for Work", 
        default=True,
        help="If True, grants up to 2800 ETB transport tax exemption. Otherwise 600 ETB.",
        tracking=True
    )
    
    # Fringe Benefits (Non-Cash)
    has_company_vehicle = fields.Boolean(
        string="Provided Company Vehicle", 
        help="Triggers a 5% Basic Salary taxable fringe benefit calculation.",
        tracking=True
    )
    company_leased_housing_rent = fields.Float(
        string="Company Leased Housing Rent", 
        help="Actual monthly rent paid by the employer for this employee's housing.",
        tracking=True
    )
    employee_housing_contribution = fields.Float(
        string="Employee Housing Contribution", 
        help="Amount deducted from the employee to offset the housing fringe benefit.",
        tracking=True
    )

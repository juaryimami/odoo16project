from odoo import models, fields, api

class EmployeeKPI(models.Model):
    _name = 'employee.kpi'
    _description = "Key Performance Evaluation Inductor"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    name = fields.Char(string='kpi')
    kpi = fields.Text(string='Key Department KPI')
    objective = fields.Text(string='Objective')
    specific_actions = fields.Char(string="Specific Actions")
    measurement_tool = fields.Char(string="Measurement Tool")
    frequency = fields.Char(string="Frequency")
    employee_id = fields.Many2one('hr.employee',string='Employee')
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id")

    from_date = fields.Date(string="From")
    end_date = fields.Date(string="To")
    target_date = fields.Date(string="Target Date")
    kpi_type = fields.Selection([
        ('personal', 'Personal'),
        ('organizational', 'Organizational'),
        ], string="Goal type")





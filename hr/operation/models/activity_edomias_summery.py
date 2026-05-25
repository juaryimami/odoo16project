from odoo import models, fields, api, _


class EmployeeActivities(models.TransientModel):
    _name = 'employee.activities.summery'
    _description = 'Piece Rate Employee Activity Summery'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    project_id = fields.Many2one('agent.project', ondelete='cascade', string='Project', required=True)
    region_id = fields.Many2one('tax.region', ondelete='cascade', string='Region')
    location_id = fields.Many2one('agent.location', ondelete='cascade', string='Location')
    activity_id = fields.Many2one('piece.rate.activity.rate',string='Activity', required=True)
    rate_id = fields.Many2one('ot.rate.list', string='Working Day Type', required=True)
    qty = fields.Float(string='Volume', required=True)
    employee_rate = fields.Float(string='Employee Rate', store=True, related='activity_id.employee_rate')
    employee_payment = fields.Float(string='Employee Payment', store=True, compute="compute_employee_payment")
    edomias_rate = fields.Float(string='Edomias Rate')
    edomias_payment = fields.Float(string='Edomias Payment')

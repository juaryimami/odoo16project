from odoo import models, fields, api, _


class EmployeeActivities(models.Model):
    _name = 'employee.activities'
    _description = 'Piece Rate Employee Activity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee',required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    project_id = fields.Many2one('agent.project', ondelete='cascade', string='Project', required=True)
    region_id = fields.Many2one('tax.region', ondelete='cascade', string='Region')
    location_id = fields.Many2one('agent.location', ondelete='cascade', string='Location')
    activity_id = fields.Many2one('piece.rate.activity.rate',string='Activity', required=True)
    rate_id = fields.Many2one('ot.rate.list', string='Working Day Type', required=True)
    qty = fields.Float(string='Volume', required=True)
    employee_rate = fields.Float(string='Employee Rate', store=True, related='activity_id.employee_rate')
    employee_payment = fields.Float(string='Employee Payment', store=True, compute="compute_employee_payment")
    edomias_rate = fields.Float(string='Edomias Rate',store=True,  related='activity_id.edomias_rate')
    edomias_payment = fields.Float(string='Edomias Payment',store=True, compute="compute_edomias_rate")

    @api.onchange('edomias_rate','rate_id','qty','activity_id')
    def compute_edomias_rate(self):
        for rec in self:
            rec.edomias_payment=rec.edomias_rate*rec.qty*rec.rate_id.rate

    @api.onchange('project_id')
    def activity_onchange_project_id(self):
        for rec in self:
            rec.activity_id = False
            if rec.project_id:
                return {
                    'domain': {
                        'activity_id': [('project_id', '=', rec.project_id.id)]
                    }
                }
            else:
                return {
                    'domain': {
                        'activity_id': []
                    }
                }

    @api.onchange('project_id')
    def location_onchange_project_id(self):
        for rec in self:
            rec.location_id = False
            if rec.project_id:
                location_ids = rec.project_id.agent_ids.mapped('location_id.id')
                return {
                    'domain': {
                        'location_id': [('id', 'in', location_ids)]
                    }
                }
            else:
                return {
                    'domain': {
                        'location_id': []
                    }
                }

    @api.onchange('project_id')
    def region_onchange_project_id(self):
        for rec in self:
            rec.region_id = False
            if rec.project_id:
                region_ids = rec.project_id.agent_ids.mapped('region_id.id')
                return {
                    'domain': {
                        'region_id': [('id', 'in', region_ids)]
                    }
                }
            else:
                return {
                    'domain': {
                        'region_id': []
                    }
                }

    @api.depends('rate_id','qty','activity_id')
    def compute_employee_payment(self):
        for rec in self:
            rec.employee_payment=rec.employee_rate*rec.qty*rec.rate_id.rate
            rec.edomias_payment = rec.edomias_rate * rec.qty * rec.rate_id.rate




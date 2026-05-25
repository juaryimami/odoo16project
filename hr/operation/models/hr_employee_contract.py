# from odoo import models, fields, api
#
# class HrContract(models.Model):
#     _inherit = 'hr.contract'
#     contract_start_date = fields.Date(string="Contract Start Date")
#     contract_end_date = fields.Date(string="Contract End Date")
#     allowance = fields.Float(string="Allowance")
#
#     project_id = fields.Many2one('agent.project', string='Project')
#     location_ids = fields.Many2many('agent.location', string='Locations')
#     job_id = fields.Many2one('hr.job', ondelete='cascade', string='Job Position', required=True)
#
#     # position_ids = fields.Many2many('edomias.position', string='Positions')
#
#     edomias_agent_id = fields.Many2one('edomias.agent', string="Edomias Agent")
#     employee_rate = fields.Float(string="Employee Rate")
#     edomias_rate = fields.Float(string="Edomias Rate")
#     quantity = fields.Float(string="Quantity", default=1.0)
#     total_edomias_rate = fields.Float(string="Total Edomias Rate", compute="_compute_total_edomias_rate", store=True)
#     total_employee_rate = fields.Float(string="Total Employee Rate", compute="_compute_total_employee_rate", store=True)
#
#
#     @api.onchange('project_id')
#     def _onchange_project(self):
#         if self.project_id:
#             self.location_ids = self.project_id.location_ids
#             self.job_id = self.project_id.job_id
#             # Update edomias related fields
#             for agent in self.env['edomias.agent'].search([('project_id', '=', self.project_id.id)]):
#                 self.edomias_agent_id = agent.id
#                 self.employee_rate = agent.employee_rate
#                 self.edomias_rate = agent.edomias_rate
#                 self.quantity = agent.quantity
#
#     @api.onchange('edomias_agent_id')
#     def _onchange_edomias_agent(self):
#         if self.edomias_agent_id:
#             self.project_id = self.edomias_agent_id.project_id.id
#             self.location_ids = self.edomias_agent_id.location_id
#             self.job_id= self.edomias_agent_id.job_id
#             self.employee_rate = self.edomias_agent_id.employee_rate
#             self.edomias_rate = self.edomias_agent_id.edomias_rate
#             self.quantity = self.edomias_agent_id.quantity
#
#     @api.depends('quantity', 'edomias_rate')
#     def _compute_total_edomias_rate(self):
#         for record in self:
#             record.total_edomias_rate = record.quantity * record.edomias_rate if record.edomias_rate else 0
#
#     @api.depends('quantity', 'employee_rate')
#     def _compute_total_employee_rate(self):
#         for record in self:
#             record.total_employee_rate = record.quantity * record.employee_rate if record.employee_rate else 0
#
#     # @api.depends('total_edomias_rate', 'total_employee_rate')
#     # def _compute_net_profit(self):
#     #     for record in self:
#     #         record.net_profit = record.total_edomias_rate - record.total_employee_rate

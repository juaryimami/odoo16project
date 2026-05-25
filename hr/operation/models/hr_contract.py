from odoo import models, fields, api,_
from odoo.exceptions import UserError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    project_id = fields.Many2one('agent.project', string='Project', required=True)
    location_id = fields.Many2one('agent.location', string='Location')

    # Wage and Allowance Fields
    wage = fields.Float(string='Salary')
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
    provident_fund = fields.Float(compute='_compute_provident_fund', string='Provident Fund(11%)')
    is_desert_area=fields.Boolean(string="is desert", compute="compute_is_deser_area")
    provision_for_leave = fields.Float(string="Provision For Leave")
    provision_for_leave_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Type', default='fixed')

    @api.depends('location_id')
    def compute_is_deser_area(self):
        for rec in self:
            if rec.location_id:
                rec.is_desert_area=rec.location_id.is_desert
            else:
                rec.is_desert_area=False


    @api.depends('desert_allowance_rate')
    def compute_desert_allowance(self):
        for rec in self:
            if rec.desert_allowance_rate:
                rec.desert_allowance=(rec.desert_allowance_rate.rate*rec.wage)/100
            else:
                rec.desert_allowance=0

    @api.onchange('project_id')
    def hr_contract_end_date(self):
        for rec in self:
            if rec.project_id:
                 rec.date_end=rec.project_id.end_date
            else:
                rec.date_end=False

    @api.onchange('project_id','location_id','job_id')
    def check_employee_on_contract(self):
        for rec in self:
            if rec.project_id.id  and rec.location_id.id and rec.job_id.id:
                contracts = self.env['hr.contract'].search(
                    [('project_id', '=', rec.project_id.id), ('location_id', '=', rec.location_id.id),
                     ('job_id', '=', rec.job_id.id)])
                agreement = self.env['edomias.agent'].search(
                    [('project_id', '=',rec.project_id.id), ('location_id', '=', rec.location_id.id),
                     ('job_id', '=', rec.job_id.id)], limit=1)
                if len(agreement) > 0:
                    if agreement.Number_of_Man_Power <= len(contracts):
                        return {
                            'warning': {
                                'title': _('Warning'),
                                'message': _("The number of contracts exceeds the number of manpower allowed by the agreement.")
                            }
                        }
                else:
                    return {
                        'warning': {
                            'title': _('Warning'),
                            'message': _("No agreement found for the selected project, location, and job.")
                        }
                    }



    @api.onchange('job_id')
    def _onchange_job_id(self):
        if self.job_id and self.project_id and self.location_id:
            agent = self.env['edomias.agent'].search([
                ('job_id', '=', self.job_id.id),
                ('project_id', '=', self.project_id.id),
                ('location_id', '=', self.location_id.id)  # Ensure it's valid for the selected location
            ], limit=1)


            # if self.project_id.modality=='piece_rate':
            #     agent = self.env['edomias.agent'].search([
            #         ('job_id', '=', self.job_id.id),
            #         ('project_id', '=', self.project_id.id),
            #         ('location_id', '=', self.location_id.id)  # Ensure it's valid for the selected location
            #     ], limit=1)
            # else:
            #     agent = self.env['edomias.agent'].search([
            #         ('job_id', '=', self.job_id.id),
            #         ('project_id', '=', self.project_id.id),
            #         ('location_id', '=', self.location_id.id)  # Ensure it's valid for the selected location
            #     ], limit=1)

            if agent:
                # Automatically fill wage and allowances based on the agent
                self.wage = agent.employee_rate
                self.hra = agent.hra
                self.da = agent.da
                self.travel_allowance = agent.travel_allowance
                self.other_allowance = agent.other_allowance
                self.project_transport_allowance = agent.project_transport_allowance
                self.project_coordination_allowance = agent.project_coordination_allowance
                self.communication_allowance = agent.communication_allowance
                self.additional_duty_allowance = agent.additional_duty_allowance

                self.hra_type = agent.hra_type
                self.da_type = agent.da_type
                self.travel_allowance_type = agent.travel_allowance_type
                self.other_allowance_type = agent.other_allowance_type

                self.project_transport_allowance_type = agent.project_transport_allowance_type
                self.project_coordination_allowance_type = agent.project_coordination_allowance_type
                self.communication_allowance_type = agent.communication_allowance_type
                self.additional_duty_allowance_type = agent.additional_duty_allowance_type
                self.provision_for_leave = agent.provision_for_leave
                self.provision_for_leave_type = agent.provision_for_leave_type
                self.meal_allowance=agent.meal_allowance
                self.meal_allowance_type=agent.meal_allowance_type

            else:
                # If no matching agent is found, reset fields
                self.wage = 0.0
                self.hra = 0.0
                self.da = 0.0
                self.travel_allowance = 0.0
                self.meal_allowance = 0.0
                self.medical_allowance = 0.0
                self.accident_allowance =0.0
                self.uniform_allowance = 0.0
                self.other_allowance = 0.0
                self.project_transport_allowance =0
                self.project_coordination_allowance = 0
                self.provision_for_severance_pay = 0
                self.communication_allowance = 0
                self.additional_duty_allowance = 0

    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id and self.project_id:
            # Check if the current job position is valid for the selected location
            valid_agents = self.env['edomias.agent'].search([
                ('project_id', '=', self.project_id.id),
                ('location_id', '=', self.location_id.id),
                ('job_id', '=', self.job_id.id)
            ])

            if not valid_agents:
                # Reset job_id, wage, and allowances if no valid agent is found for the new location
                self.job_id = False
                self.wage = 0.0
                self.hra = 0.0
                self.da = 0.0
                self.travel_allowance = 0.0
                self.meal_allowance = 0.0
                self.medical_allowance = 0.0
                self.other_allowance = 0.0

            # Additional filtering for job positions based on location
            available_jobs = self.env['edomias.agent'].search([
                ('project_id', '=', self.project_id.id),
                ('location_id', '=', self.location_id.id)
            ]).mapped('job_id')

            return {
                'domain': {
                    'job_id': [('id', 'in', available_jobs.ids)]
                }
            }
        else:
            # Clear the job position, wage, and allowances if no location is selected
            self.job_id = False
            self.wage = 0.0
            self.hra = 0.0
            self.da = 0.0
            self.travel_allowance = 0.0
            self.meal_allowance = 0.0
            self.medical_allowance = 0.0
            self.other_allowance = 0.0

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            # Filter locations and job positions based on the selected project
            return {
                'domain': {
                    'location_id': [('id', 'in', self.project_id.agent_ids.location_id.ids)],
                    'job_id': [('id', 'in', self.project_id.agent_ids.job_id.ids)]
                }
            }
        else:
            # Clear domain when no project is selected
            return {
                'domain': {
                    'location_id': [],
                    'job_id': []
                }
            }

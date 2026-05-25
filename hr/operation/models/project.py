import logging

from odoo.exceptions import ValidationError
from odoo import models, fields, api

from datetime import timedelta, date

_logger = logging.getLogger(__name__)
from odoo import models, fields, api

class EdomiasProject(models.Model):
    _name = 'agent.project'
    _description = 'Edomias Project'
    _order = 'create_date desc'

    name = fields.Char(string='Project Name', required=True)
    contract_name = fields.Char(string='Contract Name', required=True)

    description = fields.Html(string='Project Description')
    client = fields.Char(string='Client')
    client_id = fields.Many2one('res.partner', string='Client',  required=True)
    start_date = fields.Date(string='Start Date',required=True)
    end_date = fields.Date(string='End Date',required=True)
    # New Fields

    modality = fields.Selection([
        ('piece_rate', 'Piece Rate'),
        ('monthly_fee', 'Monthly Fee'),
        ('fixed-cost', 'Fixed Cost'),
        ('cost_plus', 'Cost Plus'),
        # Add more modalities as needed
    ], string='Modality', defualt='fixed-cost')

    admin_cost_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Admin Cost Type', defualt='percentage')


    renewal_date = fields.Date(string='Renewal Date')
    admin_cost = fields.Float(string='Administration Margin', required=False)
    agreement = fields.Binary(string='Agreement', attachment=True)
    is_cost_plus = fields.Boolean(string='Is Cost Plus', compute="compute_is_cost_plus")
    cost_plus_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Cost Plus Type', defualt='percentage')
    cost_plus_rate = fields.Float(string='Cost Plus Rate')

    profit_margin_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Profit and Cost Type', defualt='percentage')
    profit_margin_percentage = fields.Float(string='Profit Margin')



    create_date = fields.Datetime(string="Created Date", readonly=True, default=fields.Datetime.now)

    # Fields to select multiple locations and positions
    location_ids = fields.Many2many('agent.location', string='Locations', required=True)
    job_ids = fields.Many2one('hr.job', ondelete='cascade', string='Job Position')

    # position_ids = fields.Many2many('edomias.position', string='Positions', required=True)

    # One2many relation to hold Edomias agents
    agent_ids = fields.One2many('edomias.agent', 'project_id', string='Resources', copy=False)
    activity_ids = fields.One2many('piece.rate.activity.rate',
                                   'project_id',
                                             string='Activities', copy=False)
    renewal_ids = fields.One2many('agent.project.renewal', 'project_id', string='Renewals')

    # Renewal smart button count
    # Add a computed field for the number of renewals
    renewal_count = fields.Integer(
        string='Number of Renewals',
        compute='_compute_renewal_count',
        store=True
    )

    project_employee_count=fields.Integer(string="Employees", compute="count_employee_on_project")
    calculate_profit_margin = fields.Selection([
        ('employee_cost', 'Calculated Employee Cost'),
        ('basic_salary', 'Basic Salary'),
        ('given_employee_cost', 'Given Employee Cost'),
    ], string='Calculate Admin and  Profit Margin From',  required=True, defualt='employee_cost')

    @api.depends('modality')
    def compute_is_cost_plus(self):
        for rec in self:
            if rec.profit_margin_type=="percentage":
                rec.is_cost_plus=True
            else:
                rec.is_cost_plus = False


    def employee_list_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Employees',
                'res_model': 'hr.employee',
                'domain': [('contract_id.project_id', '=', rec.id)],
                'view_mode': 'kanban,form',
                'target': 'current'
            }

    def renewal_list_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Renewals',
                'res_model': 'agent.project.renewal',
                'domain': [('project_id', '=', rec.id)],
                'view_mode': 'tree,form',
                'target': 'current'
            }


    def count_employee_on_project(self):
        for rec in self:
            rec.project_employee_count=self.env['hr.employee'].search_count([('contract_id.project_id', '=', rec.id)])



    @api.depends('renewal_ids')
    def _compute_renewal_count(self):
        for project in self:
            project.renewal_count = len(project.renewal_ids)

    renewal_ids = fields.One2many(
        'agent.project.renewal',
        'project_id',
        string='Renewals'
    )
    @api.constrains('name', 'start_date', 'end_date')
    def _check_unique_name_and_dates(self):
        today = date.today()

        for record in self:
            # Check for unique project name
            project_with_same_name = self.search([('name', '=', record.name), ('id', '!=', record.id)])
            if project_with_same_name:
                raise ValidationError('The project name must be unique. Please choose a different name.')

            # Check if the start date is in the past
            # if record.start_date and record.start_date < today:
            #     raise ValidationError("The start date cannot be in the past. Please select a valid date.")

            # Check if the end date is in the past
            if record.end_date and record.end_date < today:
                raise ValidationError("The end date cannot be in the past. Please select a valid end date.")

            # Check if the end date is before the start date
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError(
                    "The end date cannot be earlier than the start date. Please select a valid end date.")

    @api.onchange('location_ids', 'job_ids')
    def _onchange_location_position(self):
        """ Automatically add agents when locations or positions are selected """
        agents = []

        for location in self.location_ids:
            # job_ids is a Many2one field, so you can't loop through it; just reference its id
            if self.job_ids:
                # Check if the agent already exists in the list
                if not any(agent.location_id == location and agent.job_id == self.job_ids for agent in self.agent_ids):
                    agents.append((0, 0, {
                        'location_id': location.id,
                        'job_id': self.job_ids.id,
                    }))

        # Assign the new agents list to the agent_ids field
        self.agent_ids = agents

    ### ADD THIS CODE BELOW FOR EMAIL NOTIFICATIONS ###

    @api.model
    def create(self, vals):
        # Call the original create method to save the project
        project = super(EdomiasProject, self).create(vals)

        # Call method to send notification email when a project is created
        self.send_project_creation_email(project)

        return project

    def send_project_creation_email(self, project):
        """Send notification email when a project is created."""
        try:
            users = self.env['hr.employee'].search([('job_id.name', 'in', ["Managing Director","HR Manager","Finance Manager","Section Head"])])
            for ch in users:
                location_names = [agent.location_id.name for agent in project.agent_ids if agent.location_id]
                self.env['mail.mail'].create({
                    'subject': 'ERP System Notification: New Project Created',
                    'email_from': ch.company_id.email,
                    'email_to': ch.work_email,  # Assuming Via is a user and has an email address
                    'body_html': f" Provision of {project.contract_name}service start for {project.client} at   {', '.join(location_names)} as of {project.start_date} - {project.end_date }  <br/><br/>Best regards!!",
                }).send()



        except Exception as e:
            _logger.error('Error sending email: %s', e)

    @api.model
    def check_project_end_dates(self):
        """Check for projects nearing their end date and send notifications."""
        today = fields.Date.today()
        upcoming_projects = self.search([('end_date', '<=', today + timedelta(days=30))])

        for project in upcoming_projects:
            self.send_end_date_notification(project)

    def send_end_date_notification(self, project):
        """Send email to notify about project nearing its end date."""
        try:
            users = self.env['hr.employee'].search(
                [('job_id.name', 'in', ["Managing Director", "HR Manager", "Finance Manager", "Section Head"])])
            for ch in users:
                self.env['mail.mail'].create({
                    'subject': 'Project Expiration Remainder Notification',
                    'email_from': ch.company_id.email,
                    'email_to': ch.work_email,  # Assuming Via is a user and has an email address
                    'body_html': f"Hello Dear {ch.name},<br/><br/>Project {project.name} Is Expiring  on {project.end_date} <br/><br/>Best regards!!",
                }).send()
        except Exception as e:
            _logger.error('Error sending end date email: %s', e)

    @api.model
    def toggle_column_options(self):
        # Logic to handle the toggling of column options in the view
        # This is a placeholder; implement the logic based on your needs
        pass
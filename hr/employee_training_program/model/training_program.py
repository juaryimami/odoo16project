from odoo import models, _, fields, api

class TrainingProgram(models.Model):
    _name = 'training.program'

    name = fields.Char(string="Program")

class TrainerInstitute(models.Model):
    _name = 'trainer.institute'

    name = fields.Char(string="Name")
    institute_phone_number = fields.Char(string="Institute phone number")
    address = fields.Char(string="Address")
    contact_name = fields.Many2one('res.partner',string='Contact person')
    institute_website = fields.Char(string="Website address")
    training_program = fields.Many2one('training.program', string="Training program")


class TrainingDetail(models.Model):
    _name = 'training.detail'

    name = fields.Char(string="Reference")
    program_id = fields.Many2one('training.program',string="Program")
    trainee_ids = fields.Many2many('hr.employee', string="Trainee",)
    trainer_id = fields.Many2one('res.partner', string="Trainer name")
    department_id = fields.Many2one('hr.department', string="Department")
    requested_by = fields.Many2one('hr.employee', string="Requested by")
    reason = fields.Char(string="Reason", required=False)
    institute_id = fields.Many2one('trainer.institute',string="Institute name")
    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')

    training_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),

    ], string='Training type', required=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('validate', 'Validate'),
        ('reject', 'Rejected'),
        ('progress', 'In Progress'),
        ('complete', 'Completed'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    def action_approve(self):
        for rec in self:
            rec.state = 'approve'

    def action_validate(self):
        for rec in self:
            rec.state = 'validate'

    def action_reject(self):
        for rec in self:
            rec.state = 'reject'

    def action_progress(self):
        for rec in self:
            rec.state = 'progress'

    def action_complete(self):
        for rec in self:
            rec.state = 'complete'






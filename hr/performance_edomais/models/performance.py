from odoo import models, fields, api

class Performance(models.Model):
    _name = 'employee.performance.master'
    _description = 'performance lines master'

    appraisal_id = fields.Many2one('employee.appraisal', string="Template")

    employee_id = fields.Many2one('hr.employee', related="appraisal_id.employee_id")
    name = fields.Char(string="Reference", required=True)
    position_id = fields.Many2one('hr.job', related='appraisal_id.position_id')
    work_location_id = fields.Many2one('hr.work.location', related='appraisal_id.work_location_id')
    manager_id = fields.Many2one('hr.employee', related='appraisal_id.manager_id')
    #
    meeting_date = fields.Date(string="Meeting Date", related="appraisal_id.meeting_date")

    # template_id = fields.Many2one('employee.appraisal', string="Reference")

    over_all_score = fields.Selection([
        ('excellent', 'Excellent/5'),
        ('good', 'Good/4'),
        ('satisfactory', 'Satisfactory/3'),
        ('moderate', 'Moderate/2'),
        ('insufficient', 'Insufficient/1')
        ], string="Over all score",
           compute="_compute_evaluation_result")

    appraisal_line_ids = fields.One2many('performance.lines', 'master_id',)
    # appraisal_line_id = fields.Many2many('performance.lines', )

    manager_comment = fields.Text(string="Manager Comment")
    employee_comment = fields.Text(string="Employee Comment")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('confirm', 'Confirmed'),
    ], default='draft')

    def action_submit(self):
        self.state = "submit"

    def action_approve(self):
        self.state = "approve"

    def action_confirm(self):
        self.state = "confirm"

    @api.depends('appraisal_line_ids')
    def _compute_evaluation_result(self):
        total_kpi = self.env['employee.kpi'].search([])
        for rec in self:
            success = len(rec.appraisal_line_ids.filtered(lambda line: line.success))
            partially = len(rec.appraisal_line_ids.filtered(lambda line: line.partially))
            not_success = len(rec.appraisal_line_ids.filtered(lambda line: line.not_success))
            total_point = (success*3)+(partially*2)+(not_success*1)
            max_points = len(total_kpi)*3
            weighted_score = (total_point / max_points) * 5
            if weighted_score >= 4.5:
                rec.over_all_score = 'excellent'
            elif weighted_score >= 3.5:
                rec.over_all_score = 'good'
            elif weighted_score >= 2.5:
                rec.over_all_score = 'satisfactory'
            elif weighted_score >= 1.5:
                rec.over_all_score = 'moderate'
            else:
                rec.over_all_score = 'insufficient'
















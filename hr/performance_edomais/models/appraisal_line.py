from odoo import models, fields, api


class appraisalLine(models.Model):
    _name = 'appraisal.lines'
    _description = 'Appraisal lines'
    kpi_id = fields.Many2one('employee.kpi', string="Key Dept KPI")
    evaluation_id = fields.Many2one(
        comodel_name='employee.appraisal',
        string="Evaluation",
        ondelete='cascade', index=True, copy=False)
    excellent = fields.Boolean(string="Excellent")
    very_good = fields.Boolean(string="Very good")
    good = fields.Boolean(string='Good')
    unsatisfactory = fields.Boolean(string='Unsatisfactory')
    poor = fields.Boolean(string='Poor')
    remark = fields.Char(string="Remark")
    objective = fields.Char(string="Objective", compute="compute_objective")

    @api.depends('kpi_id')
    def compute_objective(self):
        for rec in self:
            if rec.kpi_id:
                rec.objective = rec.kpi_id.objective
            else:
                rec.objective = ''

    @api.onchange('excellent')
    def _compute_excellent(self):
        for rec in self:
            if rec.excellent:
                rec.very_good = False
                rec.good = False
                rec.unsatisfactory = False
                rec.poor = False

    @api.onchange('very_good')
    def _compute_very_good(self):
        for rec in self:
            if rec.very_good:
                rec.excellent = False
                rec.good = False
                rec.unsatisfactory = False
                rec.poor = False

    @api.onchange('good')
    def _compute_good(self):
        for rec in self:
            if rec.good:
                rec.excellent = False
                rec.very_good = False
                rec.unsatisfactory = False
                rec.poor = False

    @api.onchange('unsatisfactory')
    def _compute_unsatisfactory(self):
        for rec in self:
            if rec.unsatisfactory:
                rec.excellent = False
                rec.very_good = False
                rec.good = False
                rec.poor = False

    @api.onchange('poor')
    def _compute_poor(self):
        for rec in self:
            if rec.poor:
                rec.excellent = False
                rec.very_good = False
                rec.good = False
                rec.unsatisfactory = False

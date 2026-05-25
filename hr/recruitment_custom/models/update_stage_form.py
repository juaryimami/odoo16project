from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class UpdateStageForm(models.TransientModel):
    _name = 'update.stage.form'
    _description = 'Update Stage Form'
    applicant_ids = fields.Many2many('hr.applicant', string='Applicants', required=True)
    stage_id = fields.Many2one('hr.recruitment.stage', string='Stage', required=True)

    def update_applicant_stage_form(self):
        for rec in self:
            for line in rec.applicant_ids:
                line.write({
                    'stage_id':rec.stage_id
                })


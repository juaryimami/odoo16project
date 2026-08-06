# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ChecklistTemplate(models.Model):
    _name = 'construction.checklist.template'
    _description = 'Master Checklist Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    line_ids = fields.One2many('construction.checklist.template.line', 'template_id', string='Checklist Items')
    active = fields.Boolean(default=True)

class ChecklistTemplateLine(models.Model):
    _name = 'construction.checklist.template.line'
    _description = 'Master Checklist Item'
    _order = 'sequence, id'

    template_id = fields.Many2one('construction.checklist.template', string='Template', ondelete='cascade')
    name = fields.Char(string='Checklist Item', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    mandatory = fields.Boolean(string='Mandatory', default=True)

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ConstructionLifeCycle(models.Model):
    _name = 'construction.lifecycle'
    _description = 'Construction Project Life Cycle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Life Cycle Name', required=True, placeholder="e.g. Standard 5 Cycle", tracking=True)
    phase_ids = fields.One2many('construction.phase', 'lifecycle_id', string='Cycle Phases')
    active = fields.Boolean(default=True, tracking=True)

class ConstructionPhase(models.Model):
    _name = 'construction.phase'
    _description = 'Standardized Project Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'lifecycle_id, sequence, id'

    name = fields.Char(string='Phase Name', required=True, tracking=True)
    lifecycle_id = fields.Many2one('construction.lifecycle', string='Life Cycle Template', ondelete='cascade', tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    weight = fields.Float(string='Weight (%)', default=0.0, help="Weight of this phase in the total project progress.")
    description = fields.Text(string='Description / Scope')
    active = fields.Boolean(string='Active', default=True, tracking=True)

    @api.constrains('weight')
    def _check_weights_total(self):
        for phase in self:
            if phase.lifecycle_id:
                total = sum(phase.lifecycle_id.phase_ids.mapped('weight'))
                if total > 100.001 or total < 0:
                    raise models.ValidationError(_("The total weight of phases in a Life Cycle cannot exceed 100%."))
                # We won't block 'exactly 100' here to allow incremental setup, 
                # but we'll enforce it at the project level and lifecycle 'active' status.

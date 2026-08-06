from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    project_id = fields.Many2one('project.project', string='Project')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    lifecycle_id = fields.Many2one('construction.lifecycle', string='Life Cycle', related='project_id.lifecycle_id', store=True)
    installment_line_id = fields.Many2one('real_estate.installment.line', string='Installment Line')
    installment_line_ids = fields.Many2many('real_estate.installment.line', 'account_move_installment_rel', 'move_id', 'line_id', string='Installment Lines')
    cpr_id = fields.Many2one('construction.cpr', string='Contractor Payment Request')
    payment_receipt_uploaded = fields.Boolean(string='Payment Receipt Uploaded', default=False)
    payment_token = fields.Char(string='Payment Portal Token', copy=False)
    
    # Construction Approval Workflow
    project_owner_id = fields.Many2one('res.users', string='Project Owner', related='project_id.project_owner_id', store=True)
    is_owner_approved = fields.Boolean(string='Owner Approved', default=False, tracking=True, help="Set to true when the Project Owner authorizes this bill for payment.")

    def action_post(self):
        """ Override to block posting if owner approval is required but missing. """
        for move in self:
            if move.move_type == 'in_invoice' and move.project_id and move.project_id.project_owner_id:
                if not move.is_owner_approved:
                    from odoo.exceptions import UserError
                    raise UserError(_("This construction bill (%s) requires final approval from the Project Owner (%s) before it can be posted.") % (move.name, move.project_id.project_owner_id.name))
        return super(AccountMove, self).action_post()

    def action_owner_approve(self):
        """ Final sign-off by Project Owner which triggers posting. """
        self.ensure_one()
        self.write({'is_owner_approved': True})
        return self.action_post()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    lifecycle_id = fields.Many2one('construction.lifecycle', related='move_id.lifecycle_id', store=True)
    construction_phase_id = fields.Many2one('construction.phase', string='Construction Phase')
    cost_line_id = fields.Many2one('construction.cost.sheet.line', string='Budget Line')
    cost_line_id_ref = fields.Reference(selection=[
        ('construction.cost.material.line', 'Material'),
        ('construction.cost.labor.line', 'Labor'),
        ('construction.cost.equipment.line', 'Equipment'),
        ('construction.cost.vehicle.line', 'Fleet'),
        ('construction.cost.overhead.line', 'Overhead'),
        ('construction.job.resource.line', 'Job Resource')
    ], string='Budget Reference')

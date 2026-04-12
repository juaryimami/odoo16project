# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('project.project', string='Construction Project', help="The construction project this purchase belongs to.")
    lifecycle_id = fields.Many2one('construction.lifecycle', related='project_id.lifecycle_id')
    construction_phase_id = fields.Many2one('construction.phase', string='Construction Phase', help="Specific phase this material is intended for")

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and self.project_id.analytic_account_id:
            # Propagate analytic account to all lines
            distribution = {str(self.project_id.analytic_account_id.id): 100.0}
            for line in self.order_line:
                line.analytic_distribution = distribution

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    cost_line_id = fields.Many2one('construction.cost.sheet.line', string='Budget (BOQ) Line',
                                   help="Link this purchase to a specific budget allocation")
    construction_phase_id = fields.Many2one('construction.phase', string='Construction Phase', domain="[('lifecycle_id', '=', lifecycle_id)]")
    lifecycle_id = fields.Many2one('construction.lifecycle', related='order_id.lifecycle_id')

    @api.onchange('product_id')
    def _onchange_product_id_propagate_project_analytic(self):
        if self.order_id.project_id and self.order_id.project_id.analytic_account_id:
            self.analytic_distribution = {str(self.order_id.project_id.analytic_account_id.id): 100.0}
        
        # Suggest valid BOQ line
        if self.product_id and self.order_id.project_id:
            domain = [
                ('product_id', '=', self.product_id.id),
                ('cost_sheet_id.project_id', '=', self.order_id.project_id.id)
            ]
            match = self.env['construction.cost.sheet.line'].search(domain, limit=1)
            if match:
                self.cost_line_id = match
            
            # Auto-assign phase to line if defined on header
            if self.order_id.construction_phase_id:
                self.construction_phase_id = self.order_id.construction_phase_id.id

    @api.onchange('product_qty', 'cost_line_id')
    def _onchange_check_budget_limits(self):
        if self.cost_line_id and self.product_qty > self.cost_line_id.remaining_budget_qty:
            project_name = self.order_id.project_id.name or _("Unknown Project")
            phase_name = self.cost_line_id.phase_id.name or _("N/A")
            return {
                'warning': {
                    'title': _("Budget Allocation Warning!"),
                    'message': _("Project: %s\nPhase: %s\n\nYou are requesting %.2f %s, but only %.2f units remain in the approved BOQ for '%s'. Proceeding may cause a financial variance.") % (
                        project_name, phase_name, self.product_qty, self.product_uom.name, 
                        self.cost_line_id.remaining_budget_qty, self.product_id.name
                    )
                }
            }

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
        
        if self.project_id and self.project_id.warehouse_id:
            # Automatically set the 'Deliver To' to the project's dedicated warehouse receipts
            picking_type = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.project_id.warehouse_id.id),
                ('code', '=', 'incoming')
            ], limit=1)
            if picking_type:
                self.picking_type_id = picking_type.id

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        # Find the first job order linked to any PO line
        jo = self.order_line.mapped('cost_line_id.job_order_id')[:1]
        if jo:
            res['job_order_id'] = jo.id
        elif self.project_id:
            # Fallback to any job order for this project if none found on lines (unlikely but safe)
            pass
        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    cost_line_id = fields.Many2one('construction.job.material.line', string='Budget (BOQ) Line',
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
                ('job_order_id.project_id', '=', self.order_id.project_id.id)
            ]
            match = self.env['construction.job.material.line'].search(domain, limit=1)
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
    def _prepare_invoice_line(self):
        res = super(PurchaseOrderLine, self)._prepare_invoice_line()
        if self.cost_line_id:
            master_line = self.cost_line_id.cost_line_id
            if master_line:
                res['cost_line_id_ref'] = f'construction.cost.material.line,{master_line.id}'
            
            if self.cost_line_id.job_order_id:
                # Note: This will be overwritten by other lines if they have different Job Orders, 
                # but typically a PO is for a single JO.
                self.order_id.project_id # trigger compute if needed? no.
                # Standard Odoo _prepare_invoice_line doesn't return move_id values, 
                # we rely on the header being handled or the first line winning.
                pass 
        return res

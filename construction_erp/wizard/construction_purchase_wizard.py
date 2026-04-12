# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ConstructionPurchaseWizard(models.TransientModel):
    _name = 'construction.purchase.wizard'
    _description = 'Generate PO from BOQ'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    lifecycle_id = fields.Many2one('construction.lifecycle', related='project_id.lifecycle_id', store=True)
    phase_id = fields.Many2one('construction.phase', string='Phase')
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True, domain=[('supplier_rank', '>', 0)])
    
    line_ids = fields.One2many('construction.purchase.wizard.line', 'wizard_id', string='Sourcing Lines')

    @api.onchange('project_id', 'phase_id')
    def _onchange_project_phase(self):
        if self.project_id:
            domain = [
                ('cost_sheet_id.project_id', '=', self.project_id.id),
                ('cost_type', '=', 'material'),
                ('remaining_budget_qty', '>', 0)
            ]
            if self.phase_id:
                domain.append(('phase_id', '=', self.phase_id.id))
            
            lines = self.env['construction.cost.sheet.line'].search(domain)
            wizard_lines = []
            for line in lines:
                wizard_lines.append((0, 0, {
                    'cost_line_id': line.id,
                    'product_id': line.product_id.id,
                    'qty_remaining': line.remaining_budget_qty,
                    'qty_to_order': line.remaining_budget_qty,
                }))
            self.line_ids = wizard_lines

    def action_generate_po(self):
        self.ensure_one()
        if not self.line_ids.filtered(lambda l: l.qty_to_order > 0):
            raise UserError(_("Please specify quantities to order."))

        po_vals = {
            'partner_id': self.vendor_id.id,
            'project_id': self.project_id.id,
            'task_id': self.phase_id.id if self.phase_id else False,
            'order_line': []
        }

        for line in self.line_ids.filtered(lambda l: l.qty_to_order > 0):
            po_vals['order_line'].append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.qty_to_order,
                'cost_line_id': line.cost_line_id.id,
                'price_unit': line.cost_line_id.cost_unit,
                'name': line.product_id.name,
                'date_planned': fields.Datetime.now(),
            }))

        po = self.env['purchase.order'].create(po_vals)
        
        return {
            'name': _('Purchase Order Created'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': po.id,
            'view_mode': 'form',
            'target': 'current',
        }

class ConstructionPurchaseWizardLine(models.TransientModel):
    _name = 'construction.purchase.wizard.line'
    _description = 'BOQ Sourcing Line'

    wizard_id = fields.Many2one('construction.purchase.wizard', string='Wizard')
    cost_line_id = fields.Many2one('construction.cost.sheet.line', string='Budget Line')
    product_id = fields.Many2one('product.product', string='Product', related='cost_line_id.product_id')
    qty_remaining = fields.Float(string='Remaining Budget Qty')
    qty_to_order = fields.Float(string='Qty to Order')

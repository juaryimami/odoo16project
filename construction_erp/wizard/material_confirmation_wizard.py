# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MaterialRequisitionConfirmation(models.TransientModel):
    _name = 'material.requisition.confirmation'
    _description = 'Confirm Material Delivery Split'

    requisition_id = fields.Many2one('construction.material.requisition', string='Requisition', required=True)
    line_ids = fields.One2many('material.requisition.confirmation.line', 'wizard_id', string='Materials')

    @api.model
    def default_get(self, fields):
        res = super(MaterialRequisitionConfirmation, self).default_get(fields)
        requisition_id = self._context.get('default_requisition_id')
        if requisition_id:
            req = self.env['construction.material.requisition'].browse(requisition_id)
            lines = []
            for line in req.line_ids:
                available = self.env['stock.quant']._get_available_quantity(line.product_id, req.project_id.warehouse_id.lot_stock_id)
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'requested_qty': line.quantity,
                    'available_qty': available,
                    'deliver_qty': min(line.quantity, available),
                    'purchase_qty': max(0, line.quantity - available),
                }))
            res['line_ids'] = lines
        return res

    def action_confirm(self):
        self.ensure_one()
        return self.requisition_id._process_transfer(self.requisition_id, confirmed_lines=self.line_ids)

class MaterialRequisitionConfirmationLine(models.TransientModel):
    _name = 'material.requisition.confirmation.line'
    _description = 'Material Requisition Confirmation Line'

    wizard_id = fields.Many2one('material.requisition.confirmation', string='Wizard')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    requested_qty = fields.Float(string='Requested', readonly=True)
    available_qty = fields.Float(string='Available', readonly=True)
    deliver_qty = fields.Float(string='Deliver Now')
    purchase_qty = fields.Float(string='Purchase (RFQ)')

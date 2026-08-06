# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MaterialRequisitionApproveWizard(models.TransientModel):
    _name = 'material.requisition.approve.wizard'
    _description = 'Approve Material Requisition and Select Vendors'

    requisition_id = fields.Many2one('construction.material.requisition', string='Requisition', required=True)
    line_ids = fields.One2many('material.requisition.approve.wizard.line', 'wizard_id', string='Materials')

    @api.model
    def default_get(self, fields):
        res = super(MaterialRequisitionApproveWizard, self).default_get(fields)
        requisition_id = self._context.get('default_requisition_id')
        if requisition_id:
            req = self.env['construction.material.requisition'].browse(requisition_id)
            lines = []
            for line in req.line_ids.filtered(lambda l: l.remaining_qty > 0):
                # Try to find a default vendor from the product
                default_vendor = line.product_id.seller_ids[0].partner_id if line.product_id.seller_ids else False
                
                lines.append((0, 0, {
                    'req_line_id': line.id,
                    'product_id': line.product_id.id,
                    'requested_qty': line.quantity,
                    'remaining_qty': line.remaining_qty,
                    'purchase_qty': line.remaining_qty,
                    'partner_id': default_vendor.id if default_vendor else False,
                }))
            res['line_ids'] = lines
        return res

    def action_confirm(self):
        self.ensure_one()
        from odoo.exceptions import UserError
        if not all(l.partner_id for l in self.line_ids):
            raise UserError(_("Please select a vendor for all material lines."))
        
        self.requisition_id._process_rfq_generation(self.line_ids)
        return {'type': 'ir.actions.act_window_close'}

class MaterialRequisitionApproveWizardLine(models.TransientModel):
    _name = 'material.requisition.approve.wizard.line'
    _description = 'Material Requisition Approval Line'

    wizard_id = fields.Many2one('material.requisition.approve.wizard', string='Wizard')
    req_line_id = fields.Many2one('construction.material.requisition.line', string='Original Line')
    product_id = fields.Many2one('product.product', string='Product')
    requested_qty = fields.Float(string='Requested')
    remaining_qty = fields.Float(string='Outstanding')
    purchase_qty = fields.Float(string='Approve for Purchase', required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier_rank', '>', 0)]")

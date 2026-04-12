# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MaterialRequisition(models.Model):
    _name = 'construction.material.requisition'
    _description = 'Material Requisition Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Requisition Ref', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    phase_id = fields.Many2one('construction.phase', string='Phase', tracking=True)
    job_order_id = fields.Many2one('construction.job.order', string='Job Order', tracking=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, tracking=True)
    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('partially_ordered', 'Procurement Processing'),
        ('transferred', 'Fully Transferred')
    ], string='Status', default='draft', tracking=True)

    line_ids = fields.One2many('construction.material.requisition.line', 'requisition_id', string='Materials')
    picking_ids = fields.Many2many('stock.picking', string='Store Issues')
    purchase_ids = fields.Many2many('purchase.order', string='Purchase RFQs')
    picking_count = fields.Integer(compute='_compute_picking_count')
    purchase_count = fields.Integer(compute='_compute_purchase_count')

    def _compute_picking_count(self):
        for req in self:
            req.picking_count = len(req.picking_ids)

    def _compute_purchase_count(self):
        for req in self:
            req.purchase_count = len(req.purchase_ids)

    def action_approve_and_transfer(self):
        """ Modified to support partial confirmation logic. """
        from odoo.exceptions import UserError
        for req in self:
            # Check availability
            insufficient = False
            for line in req.line_ids:
                if line.product_id.type == 'product':
                    available = self.env['stock.quant']._get_available_quantity(line.product_id, req.project_id.warehouse_id.lot_stock_id)
                    if available < line.quantity:
                        insufficient = True
                        break
            
            # If insufficient, open confirmation wizard instead of direct transfer
            if insufficient:
                return {
                    'name': _('Incomplete Stock: Delivery Preference'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'material.requisition.confirmation',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_requisition_id': req.id}
                }
            
            # Otherwise proceed standard (Full match)
            self._process_transfer(req)

    def _process_transfer(self, req, confirmed_lines=None):
        """ Internal method to handle the actual picking/PO generation with full traceability. """
        stock_lines = []
        po_lines = []
        
        project_wh = req.project_id.warehouse_id
        stock_location = project_wh.lot_stock_id
        receipt_type = self.env['stock.picking.type'].search([('warehouse_id', '=', project_wh.id), ('code', '=', 'incoming')], limit=1)
        delivery_type = self.env['stock.picking.type'].search([('warehouse_id', '=', project_wh.id), ('code', '=', 'outgoing')], limit=1)
        if not delivery_type:
            delivery_type = self.env['stock.picking.type'].search([('warehouse_id', '=', project_wh.id), ('code', '=', 'internal')], limit=1)

        # If data coming from wizard, use it. Otherwise use requisition lines.
        lines_to_process = confirmed_lines if confirmed_lines else req.line_ids
        
        for line in lines_to_process:
            product = line.product_id
            if product.type != 'product':
                stock_lines.append((product, line.quantity))
                continue
            
            if confirmed_lines:
                # Wizard results already contain split
                if line.deliver_qty > 0:
                    stock_lines.append((product, line.deliver_qty))
                if line.purchase_qty > 0:
                    po_lines.append((product, line.purchase_qty))
            else:
                # Single pass (Full availability confirmed by action_approve_and_transfer before calling this)
                stock_lines.append((product, line.quantity))

        # Carry Project / Phase / Job IDs into picking and PO
        common_vals = {
            'project_id': req.project_id.id,
            'job_order_id': req.job_order_id.id if req.job_order_id else False,
            'phase_id': req.phase_id.id if req.phase_id else False,
            'origin': req.name,
        }

        # 2. Trigger SIV Local Consumption
        if stock_lines and delivery_type:
            dest_location = self.env.ref('stock.stock_location_customers')
            picking_vals = common_vals.copy()
            picking_vals.update({
                'picking_type_id': delivery_type.id,
                'location_id': stock_location.id,
                'location_dest_id': dest_location.id,
            })
            picking = self.env['stock.picking'].create(picking_vals)
            for product, qty in stock_lines:
                self.env['stock.move'].create({
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'product_uom': product.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': stock_location.id,
                    'location_dest_id': dest_location.id,
                    'project_id': req.project_id.id, # Custom field on stock.move
                })
            req.picking_ids = [(4, picking.id)]

        # 3. Trigger SMART Purchase RFQs
        if po_lines:
            vendor = self.env['res.partner'].search([('supplier_rank', '>', 0)], limit=1)
            if not vendor:
                vendor = self.env['res.partner'].create({'name': 'Default Supplier (Auto-Generated)', 'supplier_rank': 1})
            
            po_vals = common_vals.copy()
            po_vals.update({
                'partner_id': vendor.id,
            })
            if receipt_type:
                po_vals['picking_type_id'] = receipt_type.id

            po = self.env['purchase.order'].create(po_vals)
            distribution = {str(req.project_id.analytic_account_id.id): 100.0} if req.project_id.analytic_account_id else False
            for product, qty in po_lines:
                self.env['purchase.order.line'].create({
                    'order_id': po.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_qty': qty,
                    'price_unit': product.standard_price,
                    'product_uom': product.uom_po_id.id or product.uom_id.id,
                    'date_planned': fields.Datetime.now(),
                    'project_id': req.project_id.id, # Custom field on po.line
                    'analytic_distribution': distribution,
                })
            req.purchase_ids = [(4, po.id)]
            req.state = 'partially_ordered'
        else:
            req.state = 'transferred'

    def action_view_pickings(self):
        return {
            'name': _('Store Issues / Transfers'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
        }

    def action_view_purchases(self):
        return {
            'name': _('Purchase RFQs'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.purchase_ids.ids)],
        }


class MaterialRequisitionLine(models.Model):
    _name = 'construction.material.requisition.line'
    _description = 'Material Requisition Line'

    requisition_id = fields.Many2one('construction.material.requisition', string='Requisition')
    product_id = fields.Many2one('product.product', string='Material', required=True)
    quantity = fields.Float(string='Quantity Needed', default=1.0)

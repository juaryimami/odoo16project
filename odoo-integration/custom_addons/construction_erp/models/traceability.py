# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one('project.project', string='Project', tracking=True)
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order', tracking=True)
    issue_request_id = fields.Many2one('construction.material.issue.request', string='Material Issue Request', tracking=True)
    
    is_stock_keeper = fields.Boolean(compute='_compute_is_stock_keeper')

    @api.depends_context('uid')
    def _compute_is_stock_keeper(self):
        for picking in self:
            picking.is_stock_keeper = self.env.user.has_group('construction_erp.group_construction_stock_keeper')

    @api.model
    def default_get(self, fields_list):
        res = super(StockPicking, self).default_get(fields_list)
        if 'job_order_id' in res or self._context.get('default_job_order_id'):
            jo_id = res.get('job_order_id') or self._context.get('default_job_order_id')
            jo = self.env['construction.job.order'].browse(jo_id)
            if jo:
                res.update({
                    'project_id': jo.project_id.id,
                    'phase_id': jo.phase_id.id,
                    'partner_id': self.env.user.partner_id.id,
                    'origin': jo.name,
                })
                # Auto-assign Warehouse picking type only if not already set (e.g. from context defaults)
                if jo.project_id.warehouse_id and not res.get('picking_type_id'):
                    wh = jo.project_id.warehouse_id
                    picking_type = self.env['stock.picking.type'].search([
                        ('warehouse_id', '=', wh.id),
                        ('code', '=', 'internal')
                    ], limit=1)
                    if picking_type:
                        res.update({
                            'picking_type_id': picking_type.id,
                            'location_id': picking_type.default_location_src_id.id,
                            'location_dest_id': picking_type.default_location_dest_id.id,
                        })
        return res

    def button_validate(self):
        """ Restrict validation to Stock Keepers for construction pickings. """
        for picking in self:
            if picking.job_order_id and not self.env.user.has_group('construction_erp.group_construction_stock_keeper'):
                raise models.ValidationError(_("Only authorized Stock Keepers can validate construction site transfers."))
        return super(StockPicking, self).button_validate()

    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        for picking in self:
            if picking.job_order_id:
                # Determine the Requester's name for the notification
                requester_name = self.env.user.name
                
                # Send notification to Stock Keepers
                group = self.env.ref('construction_erp.group_construction_stock_keeper')
                if group and group.users:
                    msg = _("A new material transfer request (%s) has been initiated by %s for Job Order %s. Please verify quantities and validate.") % (picking.name, requester_name, picking.job_order_id.name)
                    title = _("New Material Request: %s") % picking.name
                    for user in group.users:
                        picking.job_order_id.send_in_app_notification(user, msg, title=title)
        return res

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            if picking.issue_request_id:
                picking.issue_request_id.write({'state': 'done'})
            if picking.job_order_id:
                # Sync validated moves to Job Order Consumed Materials
                consumed_lines = []
                for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
                    # Determine cost
                    unit_price = 0.0
                    cost_line_id = False
                    
                    # Safe check for purchase_line_id (requires purchase_stock module)
                    purchase_line = getattr(move, 'purchase_line_id', False)
                    if purchase_line:
                        # Purchase Path: Use PO price
                        unit_price = purchase_line.price_unit
                    elif move.requisition_line_id:
                        # Store Issue Path: Redundant Lookup Engine
                        # Path A: Direct Requisition Link
                        req_line = move.requisition_line_id
                        if req_line.cost_line_id:
                            unit_price = req_line.cost_line_id.cost_unit
                            cost_line_id = req_line.cost_line_id.id
                        
                        # Path B: Variant-Smart Fallback Search
                        if not unit_price and picking.job_order_id:
                            # Search in Material Planning lines
                            # Try exact variant match first, then template match
                            plan_lines = picking.job_order_id.material_plan_ids
                            matching_plan = plan_lines.filtered(lambda l: l.product_id == move.product_id)
                            if not matching_plan:
                                matching_plan = plan_lines.filtered(lambda l: l.product_id.product_tmpl_id == move.product_id.product_tmpl_id)
                            
                            if matching_plan:
                                unit_price = matching_plan[0].cost_line_id.cost_unit
                                cost_line_id = matching_plan[0].cost_line_id.id
                        
                        # Increment Requisition tracking
                    
                    if not unit_price:
                        unit_price = move.product_id.standard_price
 
                    consumed_lines.append((0, 0, {
                        'product_id': move.product_id.id,
                        'quantity': move.quantity_done,
                        'unit_price': unit_price,
                    }))
                picking.job_order_id.write({'material_consumed_ids': consumed_lines})
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    requisition_line_id = fields.Many2one('construction.material.requisition.line', string='Requisition Line', ondelete='set null')
    
    planned_product_ids = fields.Many2many('product.product', compute='_compute_planned_products', string='Planned Products')

    @api.depends('picking_id.job_order_id')
    def _compute_planned_products(self):
        for move in self:
            if move.picking_id.job_order_id:
                move.planned_product_ids = move.picking_id.job_order_id.material_plan_ids.mapped('product_id').ids
            else:
                move.planned_product_ids = []

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    project_id = fields.Many2one('project.project', string='Project')
    phase_id = fields.Many2one('construction.phase', string='Phase')
    job_order_id = fields.Many2one('construction.job.order', string='Job Order')
    requisition_line_id = fields.Many2one('construction.material.requisition.line', string='Requisition Line')

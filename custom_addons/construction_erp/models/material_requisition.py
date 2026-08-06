# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MaterialRequisition(models.Model):
    _name = 'construction.material.requisition'
    _description = 'Material Requisition Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']

    name = fields.Char(string='Requisition Ref', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    project_id = fields.Many2one('project.project', string='Project', required=True, tracking=True)
    phase_id = fields.Many2one('construction.phase', string='Phase', tracking=True)
    job_order_id = fields.Many2one('construction.job.order', string='Job Order', tracking=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, tracking=True)
    date_required = fields.Date(string='Deadline (Needed By)', required=True, tracking=True, help="When these materials are needed on site.")
    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.material.requisition') or _('New')
        return super(MaterialRequisition, self).create(vals_list)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Pending PM Approval'),
        ('pm_approved', 'Pending Owner Approval'),
        ('approved', 'Approved'),
        ('partially_ordered', 'Procurement Processing'),
        ('transferred', 'Fully Transferred'),
        ('closed', 'Closed')
    ], string='Status', compute='_compute_state', store=True, default='draft', tracking=True)

    is_approved = fields.Boolean(default=False)

    @api.depends('is_approved', 'line_ids.ordered_qty', 'line_ids.transferred_qty')
    def _compute_state(self):
        for req in self:
            # Respect manual states until approval logic kicks in
            if not req.is_approved and req.state in ('draft', 'submitted'):
                # Handle initial values if needed, otherwise skip
                if not req.state:
                    req.state = 'draft'
                continue

            # Automation triggers
            if req.line_ids and all(l.transferred_qty >= l.quantity for l in req.line_ids):
                req.state = 'transferred'
            elif any(l.ordered_qty > 0 or l.transferred_qty > 0 for l in req.line_ids):
                req.state = 'partially_ordered'
            elif req.state == 'pm_approved' and not req.is_approved:
                # Stay in pm_approved until owner triggers action_approve
                pass
            elif req.is_approved:
                req.state = 'approved'
            else:
                # Fallback to current state if no triggers hit
                if not req.state:
                    req.state = 'draft'

    @api.onchange('job_order_id')
    def _onchange_job_order_id(self):
        if self.job_order_id:
            self.project_id = self.job_order_id.project_id
            self.phase_id = self.job_order_id.phase_id

    allowed_product_ids = fields.Many2many('product.product', compute='_compute_allowed_products')

    @api.depends('job_order_id', 'job_order_id.material_plan_ids')
    def _compute_allowed_products(self):
        for req in self:
            if req.job_order_id:
                req.allowed_product_ids = req.job_order_id.material_plan_ids.mapped('product_id')
            else:
                req.allowed_product_ids = self.env['product.product'].search([])

    line_ids = fields.One2many('construction.material.requisition.line', 'requisition_id', string='Materials')
    picking_ids = fields.Many2many('stock.picking', string='Store Issues')
    purchase_ids = fields.Many2many('purchase.order', string='Purchase RFQs')
    picking_count = fields.Integer(compute='_compute_picking_count')
    purchase_count = fields.Integer(compute='_compute_purchase_count')
    show_outstanding_action = fields.Boolean(compute='_compute_show_outstanding')

    def _compute_show_outstanding(self):
        for req in self:
            # Show button only if there is actually something left to buy/issue
            req.show_outstanding_action = any(line.remaining_qty > 0 for line in req.line_ids)

    def _compute_picking_count(self):
        for req in self:
            req.picking_count = len(req.picking_ids)

    def _compute_purchase_count(self):
        for req in self:
            req.purchase_count = len(req.purchase_ids)

    def action_submit(self):
        self.ensure_one()
        if not self.line_ids:
            from odoo.exceptions import UserError
            raise UserError(_("You cannot submit an empty requisition."))
        
        self.write({'state': 'submitted'})
        
        # Notify Project Manager
        if self.project_id.user_id:
            msg = _("Material Requisition %s has been submitted for your approval.") % self.name
            title = _("Requisition Approval Required")
            self.send_in_app_notification(self.project_id.user_id, msg, title=title)

    def action_pm_approve(self):
        self.ensure_one()
        self.write({'state': 'pm_approved'})
        
        # Notify Owner
        owner = self.project_id.project_owner_id
        if owner:
            msg = _("Material Requisition %s has been approved by PM and requires your final sign-off.") % self.name
            title = _("Procurement Approval Required")
            self.send_in_app_notification(owner, msg, title=title)
            self.notify_contact(owner.partner_id, msg, title=title)

    def action_approve(self):
        self.ensure_one()
        if self.state != 'pm_approved':
            from odoo.exceptions import UserError
            raise UserError(_("Material Requisition must be approved by the Project Manager before Owner approval."))
            
        return {
            'name': _('Material Requisition: Vendor Selection'),
            'type': 'ir.actions.act_window',
            'res_model': 'material.requisition.approve.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_requisition_id': self.id}
        }

    def _process_transfer(self, req, confirmed_lines=None):
        """ Internal method to handle the actual picking/PO generation with full traceability. """
        stock_lines = []
        po_lines = []
        
        project_wh = req.project_id.warehouse_id
        if not project_wh:
            from odoo.exceptions import UserError
            raise UserError(_("Logistics Error: No 'Dedicated Site Warehouse' found for project '%s'. Please assign a warehouse in the Project form before approving transfers.") % req.project_id.name)
        
        stock_location = project_wh.lot_stock_id
        if not stock_location:
            from odoo.exceptions import UserError
            raise UserError(_("Configuration Error: The warehouse '%s' has no stock location defined. Please check warehouse settings.") % project_wh.name)

        receipt_type = self.env['stock.picking.type'].search([('warehouse_id', '=', project_wh.id), ('code', '=', 'incoming')], limit=1)
        delivery_type = self.env['stock.picking.type'].search([('warehouse_id', '=', project_wh.id), ('code', '=', 'outgoing')], limit=1)
        if not delivery_type:
            delivery_type = self.env['stock.picking.type'].search([('warehouse_id', '=', project_wh.id), ('code', '=', 'internal')], limit=1)

        # If data coming from wizard, use it. Otherwise use requisition lines.
        lines_to_process = confirmed_lines if confirmed_lines else req.line_ids
        
        updated_lines = []
        for line in lines_to_process:
            # Match back to main requisition line
            main_line = line.req_line_id if hasattr(line, 'req_line_id') else line
            
            product = main_line.product_id
            
            # 1. Determine quantities
            d_qty = line.deliver_qty if hasattr(line, 'deliver_qty') else main_line.remaining_qty
            p_qty = line.purchase_qty if hasattr(line, 'purchase_qty') else 0
            
            if d_qty > 0:
                stock_lines.append((product, d_qty, main_line))
            if p_qty > 0:
                po_lines.append((product, p_qty, main_line))

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
            for product, qty, main_line in stock_lines:
                self.env['stock.move'].create({
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'product_uom': product.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': stock_location.id,
                    'location_dest_id': dest_location.id,
                    'project_id': req.project_id.id,
                    'phase_id': req.phase_id.id if req.phase_id else False,
                    'job_order_id': req.job_order_id.id if req.job_order_id else False,
                    'requisition_line_id': main_line.id,
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
            for product, qty, main_line in po_lines:
                self.env['purchase.order.line'].create({
                    'order_id': po.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_qty': qty,
                    'price_unit': product.standard_price,
                    'product_uom': product.uom_po_id.id or product.uom_id.id,
                    'date_planned': fields.Datetime.now(),
                    'project_id': req.project_id.id,
                    'analytic_distribution': distribution,
                    'cost_line_id': main_line.cost_line_id.id if main_line.cost_line_id else False,
                    'requisition_line_id': main_line.id,
                })
                # Update tracking
                main_line.ordered_qty += qty
                
            req.purchase_ids = [(4, po.id)]
            req.state = 'partially_ordered'
        
        # Check if fully finished
        if all(l.remaining_qty <= 0 for l in req.line_ids):
            req.state = 'transferred'
        elif any(l.ordered_qty > 0 for l in req.line_ids):
            req.state = 'partially_ordered'

    def _process_rfq_generation(self, wizard_lines):
        """ Creates Purchase RFQs grouped by vendor. Skipping SIV as requested. """
        self.ensure_one()
        
        # Group by partner
        vendors = {}
        for w_line in wizard_lines:
            if w_line.purchase_qty > 0:
                partner = w_line.partner_id
                if partner not in vendors:
                    vendors[partner] = []
                vendors[partner].append(w_line)
        
        distribution = {str(self.project_id.analytic_account_id.id): 100.0} if self.project_id.analytic_account_id else False

        for partner, lines in vendors.items():
            po_lines_vals = []
            for line in lines:
                product = line.product_id or line.req_line_id.product_id
                po_lines_vals.append((0, 0, {
                    'product_id': product.id,
                    'name': product.display_name or product.name or _("Material"),
                    'product_qty': line.purchase_qty,
                    'price_unit': product.standard_price,
                    'product_uom': product.uom_po_id.id or product.uom_id.id,
                    'date_planned': fields.Datetime.to_datetime(self.date_required) if self.date_required else fields.Datetime.now(),
                    'project_id': self.project_id.id,
                    'analytic_distribution': distribution,
                    'cost_line_id': line.req_line_id.cost_line_id.id if line.req_line_id.cost_line_id else False,
                    'requisition_line_id': line.req_line_id.id,
                }))

            po_vals = {
                'partner_id': partner.id,
                'origin': self.name,
                'project_id': self.project_id.id,
                'job_order_id': self.job_order_id.id if self.job_order_id else False,
                'phase_id': self.phase_id.id if self.phase_id else False,
                'date_planned': fields.Datetime.to_datetime(self.date_required) if self.date_required else fields.Datetime.now(),
                'order_line': po_lines_vals,
            }
            if self.project_id.warehouse_id:
                picking_type = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', self.project_id.warehouse_id.id),
                    ('code', '=', 'incoming')
                ], limit=1)
                if picking_type:
                    po_vals['picking_type_id'] = picking_type.id
            po = self.env['purchase.order'].create(po_vals)
            self.purchase_ids = [(4, po.id)]
        
        # Mark as approved to trigger state computation
        self.write({'is_approved': True})
        
        # Notify Purchasing Managers of the created RFQs
        group = self.env.ref('purchase.group_purchase_manager')
        if group and group.users:
            msg = _("Material Requisition %s has been approved by the Project Owner. Purchase RFQs have been successfully generated.") % self.name
            title = _("Requisition Approved: RFQs Generated")
            for user in group.users:
                self.send_in_app_notification(user, msg, title=title)

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

    @api.model
    def _cron_check_requisition_deadlines(self):
        """ Smart Reminder logic for overdue requisitions. """
        reminder_days = int(self.env['ir.config_parameter'].sudo().get_param('construction_erp.requisition_reminder_days', 3))
        limit_date = fields.Date.today() + fields.Date.to_relativedelta(days=reminder_days)
        
        # We check approved/submitted requisitions that are not fully ordered
        requisitions = self.search([
            ('state', 'in', ['submitted', 'approved', 'partially_ordered']),
            ('date_required', '<=', limit_date)
        ])
        
        for req in requisitions:
            # Check if RFQs are confirmed. If at least one RFQ is still in 'draft' or 'sent', we remind.
            pending_rfqs = req.purchase_ids.filtered(lambda p: p.state in ['draft', 'sent'])
            
            if req.state == 'submitted' or pending_rfqs:
                summary = "DEADLINE REMINDER: Material Requisition"
                note = f"Requisition {req.name} is approaching its deadline ({req.date_required}). "
                if req.state == 'submitted':
                    note += "It is still pending approval."
                else:
                    note += f"Associated RFQs ({', '.join(pending_rfqs.mapped('name'))}) are not yet confirmed."
                
                # Assign activity to PM
                if req.project_id.user_id:
                    # Check if activity already exists
                    existing = self.env['mail.activity'].search([
                        ('res_id', '=', req.id),
                        ('res_model_id', '=', self.env.ref('construction_erp.model_construction_material_requisition').id),
                        ('summary', '=', summary),
                        ('user_id', '=', req.project_id.user_id.id)
                    ])
                    if not existing:
                        req.activity_schedule(
                            'mail.mail_activity_data_todo',
                            user_id=req.project_id.user_id.id,
                            summary=summary,
                            note=note,
                            date_deadline=req.date_required
                        )


class MaterialRequisitionLine(models.Model):
    _name = 'construction.material.requisition.line'
    _description = 'Material Requisition Line'

    requisition_id = fields.Many2one('construction.material.requisition', string='Requisition')
    product_id = fields.Many2one('product.product', string='Material', required=True)
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.requisition_id.job_order_id:
            # Domain is enforced in XML, this is for server-side if needed or simple validation
            plan_products = self.requisition_id.job_order_id.material_plan_ids.mapped('product_id.id')
            if self.product_id and self.product_id.id not in plan_products:
                return {'warning': {
                    'title': _("Warning"),
                    'message': _("This product is not part of the Job Order's material plan.")
                }}

    quantity = fields.Float(string='Quantity Needed', default=1.0)
    
    transferred_qty = fields.Float(string='Issued Qty', compute='_compute_transferred', store=True)
    ordered_qty = fields.Float(string='Purchased Qty', compute='_compute_ordered', store=True)
    direct_issued_qty = fields.Float(string='Direct Issued Qty', compute='_compute_transferred', store=True)
    remaining_qty = fields.Float(string='Outstanding Qty', compute='_compute_remaining', store=True)

    purchase_line_ids = fields.One2many('purchase.order.line', 'requisition_line_id', string='Purchase Lines')
    move_ids = fields.One2many('stock.move', 'requisition_line_id', string='Stock Moves')

    cost_line_id = fields.Many2one('construction.job.material.line', string='Plan Line', 
                                  compute='_compute_cost_line', store=True, readonly=False, ondelete='set null')

    @api.depends('product_id', 'requisition_id.job_order_id')
    def _compute_cost_line(self):
        for line in self:
            if line.product_id and line.requisition_id.job_order_id:
                # Auto-link to budget line if found in job order plans
                plan = line.requisition_id.job_order_id.material_plan_ids.filtered(
                    lambda l: l.product_id == line.product_id
                )
                if plan:
                    line.cost_line_id = plan[0].id
                else:
                    line.cost_line_id = False
            else:
                line.cost_line_id = False

    @api.depends('purchase_line_ids.product_qty', 'purchase_line_ids.state')
    def _compute_ordered(self):
        for line in self:
            # Sum up matching PO lines (ONLY confirmed/done POs)
            active_po_lines = line.purchase_line_ids.filtered(lambda l: l.state in ('purchase', 'done'))
            line.ordered_qty = sum(active_po_lines.mapped('product_qty'))

    @api.depends('move_ids.quantity_done', 'move_ids.state', 
                 'purchase_line_ids.move_ids.quantity_done', 'purchase_line_ids.move_ids.state')
    def _compute_transferred(self):
        for line in self:
            # Source A: Direct Store Issues (SIV)
            direct_moves = line.move_ids.filtered(lambda m: m.state == 'done')
            
            # Source B: Purchase Order Receipts
            po_moves = line.purchase_line_ids.mapped('move_ids').filtered(lambda m: m.state == 'done')
            
            # Real total Issued to site
            line.transferred_qty = sum(direct_moves.mapped('quantity_done')) + sum(po_moves.mapped('quantity_done'))
            
            # Tracking specifically what didn't come from a PO (for procurement calculation)
            # SIV moves usually don't have purchase_line_id
            siv_moves = direct_moves.filtered(lambda m: not m.purchase_line_id)
            line.direct_issued_qty = sum(siv_moves.mapped('quantity_done'))

    @api.depends('quantity', 'direct_issued_qty', 'ordered_qty')
    def _compute_remaining(self):
        for line in self:
            # Remaining to Acquire = Total Needed - (What we already bought + What we already took from store)
            line.remaining_qty = max(0, line.quantity - (line.ordered_qty + line.direct_issued_qty))

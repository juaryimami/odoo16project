# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import models, fields, api, _
# pyrefly: ignore [missing-import]
from odoo.exceptions import UserError

class ConstructionMaterialIssueRequest(models.Model):
    _name = 'construction.material.issue.request'
    _description = 'Material Stock Issue Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'construction.notification.mixin']
    _order = 'id desc'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    job_order_id = fields.Many2one('construction.job.order', string='Job Order', required=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Project', related='job_order_id.project_id', store=True, readonly=True)
    phase_id = fields.Many2one('construction.phase', string='Phase', related='job_order_id.phase_id', store=True, readonly=True)
    
    request_type = fields.Selection([
        ('return', 'Return'),
        ('delivery', 'Delivery')
    ], string='Request Type', default='delivery', required=True, tracking=True)
    
    description = fields.Text(string='Request Description')
    time_needed = fields.Datetime(string='Time Needed', default=fields.Datetime.now, required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    line_ids = fields.One2many('construction.material.issue.request.line', 'request_id', string='Material Lines')
    picking_ids = fields.One2many('stock.picking', 'issue_request_id', string='Stock Pickings')
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking Count')

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.material.issue.request') or _('New')
        return super(ConstructionMaterialIssueRequest, self).create(vals_list)

    def action_submit(self):
        self.ensure_one()
        self.write({'state': 'requested'})
        # Notification to Project Manager
        pm = self.project_id.user_id
        if pm:
            self.send_in_app_notification(
                pm,
                _("A new Material Stock Issue Request %s has been submitted for your approval.") % self.name,
                title=_("Material Issue Approval Required")
            )

    def action_approve(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("You cannot approve a request without any material lines."))
            
        if not self.project_id.warehouse_id:
            raise UserError(_("Logistics Error: No 'Dedicated Site Warehouse' found for project '%s'. Please assign a warehouse in the Project form before approving.") % self.project_id.name)
        
        project_wh = self.project_id.warehouse_id
        
        # Determine picking type based on request_type (Return or Delivery)
        if self.request_type == 'return':
            # 1. Search for a picking type named 'Returns' or 'Return' for this warehouse
            picking_type = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', project_wh.id),
                ('code', '=', 'incoming'),
                ('name', 'ilike', 'return')
            ], limit=1)
            # 2. Fallback to warehouse in_type_id
            if not picking_type:
                picking_type = project_wh.in_type_id
            # 3. Fallback to any incoming picking type for this warehouse
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', project_wh.id),
                    ('code', '=', 'incoming')
                ], limit=1)
            # 4. Global fallback
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
            if not picking_type:
                raise UserError(_("Configuration Error: No 'Receipt/Return' picking type found for warehouse '%s'.") % project_wh.name)
            
            source_location = picking_type.default_location_src_id or self.env.ref('stock.stock_location_customers', raise_if_not_found=False) or self.env.ref('stock.stock_location_suppliers')
            dest_location = project_wh.lot_stock_id
            
            # Return address should be the project's warehouse partner
            picking_partner = self.project_id.warehouse_id.partner_id.id or self.project_id.partner_id.id
            
        else: # delivery
            # 1. Search for warehouse out_type_id
            picking_type = project_wh.out_type_id
            # 2. Search for picking type with code 'outgoing' for this warehouse
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search([
                    ('warehouse_id', '=', project_wh.id),
                    ('code', '=', 'outgoing')
                ], limit=1)
            # 3. Global fallback
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
            if not picking_type:
                raise UserError(_("Configuration Error: No 'Delivery' picking type found for warehouse '%s'.") % project_wh.name)
                
            source_location = project_wh.lot_stock_id
            dest_location = picking_type.default_location_dest_id or self.env.ref('stock.stock_location_customers')
            
            # Delivery address should be the project's partner
            picking_partner = self.project_id.partner_id.id

        # Create Draft Picking
        picking = self.env['stock.picking'].create({
            'job_order_id': self.job_order_id.id,
            'project_id': self.project_id.id,
            'phase_id': self.phase_id.id,
            'issue_request_id': self.id,
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'partner_id': picking_partner,
            'origin': self.name,
            'move_ids_without_package': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
                'project_id': self.project_id.id,
                'phase_id': self.phase_id.id,
                'job_order_id': self.job_order_id.id,
            }) for line in self.line_ids]
        })
        picking.action_confirm()
        
        self.write({'state': 'approved'})
        
        # Notify Stock Keeper
        group = self.env.ref('construction_erp.group_construction_stock_keeper')
        if group and group.users:
            # Determine the Requester's name for the notification
            requester_name = self.env.user.name
            msg = _("A new material transfer request (%s) has been initiated by %s for Job Order %s. Please verify quantities and validate.") % (picking.name, requester_name, self.job_order_id.name)
            title = _("New Material Request: %s") % picking.name
            for user in group.users:
                self.send_in_app_notification(user, msg, title=title)
            
        return True

    def action_reject(self):
        self.ensure_one()
        self.write({'state': 'rejected'})

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['domain'] = [('issue_request_id', '=', self.id)]
        action['context'] = {'default_issue_request_id': self.id}
        return action

class ConstructionMaterialIssueRequestLine(models.Model):
    _name = 'construction.material.issue.request.line'
    _description = 'Material Stock Issue Request Line'

    request_id = fields.Many2one('construction.material.issue.request', string='Request Reference', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

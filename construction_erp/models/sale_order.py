from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one('project.project', string='Source Project', help="The construction project this sale belongs to.")
    unit_id = fields.Many2one('real_estate.unit', string='Property Unit Type', domain="[('project_id', '=', project_id)]")

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and self.project_id.analytic_account_id:
            # Propagate analytic account to all lines
            distribution = {str(self.project_id.analytic_account_id.id): 100.0}
            for line in self.order_line:
                line.analytic_distribution = distribution

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        if self.unit_id:
            # Check availability
            if self.unit_id.quantity_available <= 0:
                return {'warning': {
                    'title': _('Stock Alert'),
                    'message': _('This unit type is currently SOLD OUT in this project.')
                }}
            
            if self.unit_id.product_id:
                # Prepare analytic distribution if project is set
                distribution = False
                if self.project_id and self.project_id.analytic_account_id:
                    distribution = {str(self.project_id.analytic_account_id.id): 100.0}

                # Add the unit product to the sale order lines
                self.order_line = [(0, 0, {
                    'product_id': self.unit_id.product_id.product_variant_id.id if self.unit_id.product_id.product_variant_id else False,
                    'name': self.unit_id.product_id.name + " (Unit Profile: " + self.unit_id.name + ")",
                    'product_uom_qty': 1,
                    'price_unit': self.unit_id.price,
                    'analytic_distribution': distribution,
                })]

    def action_confirm(self):
        for order in self:
            if order.unit_id:
                # Sum quantity of lines belonging to this unit type
                requested_qty = sum(order.order_line.filtered(
                    lambda l: l.product_id.product_tmpl_id.id == order.unit_id.product_id.id
                ).mapped('product_uom_qty'))
                
                if order.unit_id.quantity_available < requested_qty:
                    raise UserError(_(
                        "Insufficient inventory in project pool! \n\n"
                        "Project: %s\n"
                        "Unit Profile: %s\n"
                        "Available: %s\n"
                        "Requested: %s"
                    ) % (order.project_id.name, order.unit_id.name, order.unit_id.quantity_available, requested_qty))
                    
        return super(SaleOrder, self).action_confirm()

    def action_view_installment_plan(self):
        self.ensure_one()
        plan = self.env['real_estate.installment.plan'].search([('sale_id', '=', self.id)], limit=1)
        if plan:
            return {
                'name': 'Installment Plan',
                'type': 'ir.actions.act_window',
                'res_model': 'real_estate.installment.plan',
                'res_id': plan.id,
                'view_mode': 'form',
            }
        else:
            return {
                'name': 'Create Installment Plan',
                'type': 'ir.actions.act_window',
                'res_model': 'real_estate.installment.plan',
                'view_mode': 'form',
                'context': {
                    'default_sale_id': self.id,
                    'default_unit_id': self.unit_id.id,
                    'default_client_id': self.partner_id.id,
                }
            }

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    project_available_qty = fields.Integer(
        string='Project Available', 
        related='order_id.unit_id.quantity_available', 
        readonly=True,
        help="Remaining units of this type within the selected construction project pool."
    )

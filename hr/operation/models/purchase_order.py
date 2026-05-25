from odoo import models, fields, api

# Extending the Purchase Order model
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('agent.project', string='Project')
    location_id = fields.Many2one('agent.location', string='Location')
    cost_plus = fields.Float(string='Cost Plus', compute='_compute_cost_plus')

    @api.depends('project_id', 'order_line.price_unit')
    def _compute_cost_plus(self):
        for order in self:
            if order.project_id:
                profit_margin = order.project_id.profit_margin_percentage or 1
                # Apply percentage calculation
                profit_margin_percentage = profit_margin / 100
                for line in order.order_line:
                    line.cost_plus = line.price_unit + (line.price_unit * profit_margin_percentage)
            else:
                for line in order.order_line:
                    line.cost_plus = line.price_unit


# Extending the Purchase Order Line model
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    cost_plus = fields.Float(string='Cost Plus', compute='_compute_cost_plus', store=True)
    profit_margin_percentage = fields.Float(string='Profit Margin Percentage', related='order_id.project_id.profit_margin_percentage', readonly=True)

    @api.depends('price_unit', 'order_id.project_id')
    def _compute_cost_plus(self):
        for line in self:

            project = line.order_id.project_id
            if project and project.profit_margin_type=="percentage":
                # Apply percentage as part of the cost_plus calculation
                profit_margin = project.profit_margin_percentage / 100
                line.cost_plus = line.price_unit + (line.price_unit * profit_margin)
            else:
                # Default to price_unit if no profit margin set
                line.cost_plus = line.price_unit

    @api.depends('cost_plus', 'price_unit', 'product_qty')
    def _compute_amount(self):
        """ Override the subtotal calculation to use cost_plus if a profit margin is set. """
        for line in self:
            project = line.order_id.project_id
            if project and project.profit_margin_type=="percentage":
                # Use cost_plus for the subtotal calculation if profit_margin_percentage is set
                line.price_subtotal = line.cost_plus * line.product_qty
            else:
                # Default to price_unit if no profit margin is set
                line.price_subtotal = line.price_unit * line.product_qty

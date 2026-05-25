from zeep.xsd import String

from odoo import models, fields, api
from odoo.exceptions import ValidationError

# Extending the Purchase Order model
class CustomSalesOrder(models.Model):
    _inherit = 'sale.order'

    operation_id = fields.Many2one('agent.project', string='Project')
    client = fields.Char(string='Client')
    location_id = fields.Many2one('agent.location', string='Location')
    admin_cost = fields.Float(string="Administration Cost")
    profit_margin = fields.Float(string="Profit Margin")
    profit_margin_type = fields.Selection([
        ('percentage', 'Percentage(%)'),
        ('fixed', 'Fixed'),
    ], string='Profit and Cost Type', defualt='percentage')
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date From")
    is_piece_rate=fields.Float(String="is piece rate", compute="compute_is_piece_rate")

    @api.depends('operation_id')
    def compute_is_piece_rate(self):
        for rec in self:
            if rec.operation_id.modality=="piece_rate":
                rec.is_piece_rate=True
            else:
                rec.is_piece_rate=False




    @api.onchange('operation_id','location_id')
    def return_product_line(self):
        product_lines = []
        for rec in self:
            if rec.operation_id.modality=="piece_rate":
                if not (rec.date_from and rec.date_to ):
                    raise ValidationError('Please Select Date Rage')
            rec.order_line = False
            rec.partner_id=rec.operation_id.client_id
            rec.admin_cost=rec.operation_id.admin_cost
            rec.profit_margin=rec.operation_id.profit_margin_percentage
            rec.profit_margin_type=rec.operation_id.profit_margin_type
            if rec.operation_id and rec.operation_id.modality!="piece_rate":
                for line in rec.operation_id.agent_ids:
                    product_lines.append((0, 0, {
                        'product_template_id': line.service_id.product_tmpl_id.id,
                        'product_id': line.service_id.id,
                        'name': f"{line.service_id.name} ({line.location_id.name})",
                        'product_uom_qty': line.Number_of_Man_Power,
                        'price_unit': line.edomias_rate,
                        'admin_cost': rec.operation_id.admin_cost,
                        'profit_margin': rec.operation_id.profit_margin_percentage,
                    }))
            else:
                activities=self.compute_and_return_activity_list()
                for key, activity in activities.items():
                    product_lines.append((0, 0, {
                        'product_template_id':activity['product_template_id'],
                        'product_id': activity['product_id'],
                        'name': activity['name'],
                        'product_uom_qty': activity['total_qty'],
                        'price_unit':activity['edomias_rate'],
                        'rate_id':activity['rate_id'],

                    }))
            rec.order_line = product_lines


    def compute_and_return_activity_list(self):
        activity_dict = {}
        for rec in self:
           activities= self.env['employee.activities'].search([('project_id','=', rec.operation_id.id),
                                                    ('date', '>=', rec.date_from), ('date', '<=', rec.date_to)])
           for activity in activities:
               key = (activity.rate_id.id, activity.activity_id.id)  # Create a tuple for the key
               if key not in activity_dict:
                   activity_dict[key] = {'rate_id': activity.rate_id.id,
                                         'activity_id': activity.activity_id.id,
                                         'product_template_id': activity.activity_id.service_id.product_tmpl_id.id,
                                         'product_id': activity.activity_id.service_id.id,
                                         'edomias_rate': activity.edomias_rate,
                                         'name': f"{activity.activity_id.service_id.name} ({self.location_id.name})",
                                         'total_qty': 0.0}

               activity_dict[key]['total_qty'] += activity.qty

        return activity_dict

class InheritSalesOrderLine(models.Model):
    _inherit = 'sale.order.line'
    admin_cost = fields.Float(string="Administration Cost")
    profit_margin = fields.Float(string="Profit Margin")
    rate_id = fields.Many2one('ot.rate.list', string='Working Day Type', required=True)

    # @api.onchange('price_unit','order_id')
    # def compute_admin_cost(self):
    #     for rec in self:
    #         if rec.order_id.operation_id.modality=="cost_plus":
    #            rec.admin_cost=(rec.price_unit*rec.order_id.operation_id.cost_plus_rate)/100
    #         else:
    #             rec.admin_cost = 0
    #
    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','admin_cost')
    # def _compute_amount(self):
    #     """
    #     Compute the amounts of the SO line.
    #     """
    #     for line in self:
    #         tax_results = self.env['account.tax'].with_company(line.company_id)._compute_taxes(
    #             [line._convert_to_tax_base_line_dict()]
    #         )
    #         totals = list(tax_results['totals'].values())[0]
    #         amount_untaxed = totals['amount_untaxed'] + (line.product_uom_qty * line.admin_cost)
    #         amount_tax = totals['amount_tax']
    #
    #         line.update({
    #             'price_subtotal': amount_untaxed,
    #             'price_tax': amount_tax,
    #             'price_total': amount_untaxed + amount_tax,
    #         })

    # @api.onchange('admin_cost')
    # def compute_subtotal(self):
    #     for rec in self:
    #         rec.price_unit=rec.price_unit + rec.admin_cost






from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Add new fields to configuration settings to Restrict stock warehouse
    for users."""
    _inherit = 'res.config.settings'

    group_user_warehouse_restriction = fields.Boolean(
        string="Restrict Stock Warehouse",
        implied_group='user_warehouse_restriction.'
                      'user_warehouse_restriction_group_user',
        help="Check if you want to restrict warehouse for users.")

    @api.onchange('group_user_warehouse_restriction')
    def _onchange_group_user_warehouse_restriction(self):
        """This method is triggered when the 'group_user_warehouse_restriction'
        field is changed. if it's true, assigns the current user as the
        allowed user of all existing warehouses."""
        warehouses = self.env['stock.warehouse'].search([])
        for warehouse in warehouses:
            if self.group_user_warehouse_restriction:
                # Assign the current user to each warehouse
                warehouse.user_ids = [(6, 0, [self.env.user.id])]
            else:
                # Clear the allowed users for each warehouse
                warehouse.user_ids = [(5, 0, 0)]

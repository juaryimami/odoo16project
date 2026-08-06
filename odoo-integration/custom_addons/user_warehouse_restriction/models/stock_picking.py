# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models


class StockPicking(models.Model):
    """Extends stock picking to apply domain restrictions based on user's
    assigned warehouses."""
    _inherit = 'stock.picking'

    @api.onchange('location_id', 'location_dest_id', 'picking_type_id')
    def _onchange_location_id(self):
        """Domain for location_id and location_dest_id.
        Allow picking locations from other warehouses ONLY if it's an internal transfer.
        """
        if self.env.user.has_group('user_warehouse_restriction.user_warehouse_restriction_group_user'):
            is_internal = self.picking_type_id.code == 'internal'
            
            # Base domain: Locations in allowed warehouses
            base_domain = [('warehouse_id.user_ids', 'in', self.env.user.id)]
            
            if is_internal:
                # For internal transfers, allow picking from/to ANY location
                # The record rules will still restrict visibility, but this allows 
                # selecting a 'Partner' or 'Other Project' location if needed.
                # Actually, we should allow ANY location so they can pick a destination in another WH.
                return {
                    'domain': {
                        'location_id': ['|'] + base_domain + [('warehouse_id', '!=', False)],
                        'location_dest_id': ['|'] + base_domain + [('warehouse_id', '!=', False)]
                    }
                }
            
            return {
                'domain': {
                    'location_id': base_domain,
                    'location_dest_id': base_domain
                }
            }



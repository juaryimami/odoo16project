# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import http, _
# pyrefly: ignore [missing-import]
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
# pyrefly: ignore [missing-import]
from odoo.http import request

class RealEstateCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        # We'll count the number of sales orders for this partner that are confirmed (sale or done)
        if 'property_count' in counters:
            property_count = request.env['sale.order'].search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['sale', 'done']),
                ('unit_id', '!=', False)  # Ensure it's a real estate sale
            ])
            values['property_count'] = property_count

        return values

    @http.route(['/my/properties', '/my/properties/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_properties(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done']),
            ('unit_id', '!=', False)
        ]

        # count for pager
        property_count = SaleOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/properties",
            total=property_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        properties = SaleOrder.search(domain, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'properties': properties,
            'page_name': 'property',
            'pager': pager,
            'default_url': '/my/properties',
        })
        return request.render("construction_erp.portal_my_properties", values)

    @http.route(['/my/property/<int:order_id>'], type='http', auth="user", website=True)
    def portal_property_dashboard(self, order_id, **kw):
        from werkzeug.exceptions import NotFound
        sale_order = request.env['sale.order'].sudo().browse(order_id)
        if not sale_order.exists() or sale_order.partner_id != request.env.user.partner_id:
            raise NotFound()
            
        # Get Installment Plan
        plan = request.env['real_estate.installment.plan'].sudo().search([('sale_id', '=', sale_order.id)], limit=1)
        
        # Get Invoices - Using invoice_origin OR partner and project
        invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('project_id', '=', sale_order.project_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel')
        ])
        
        # Get Documents (Attachments on the SO)
        documents = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', sale_order.id),
            ('type', '=', 'binary') # only files
        ])
        
        # Financials
        total_paid = sum(inv.amount_total - inv.amount_residual for inv in invoices.filtered(lambda i: i.state == 'posted'))
        total_amount = sale_order.amount_total
        remaining_balance = total_amount - total_paid
        progress_pct = (total_paid / total_amount * 100) if total_amount > 0 else 0

        values = self._prepare_portal_layout_values()
        values.update({
            'sale_order': sale_order,
            'plan': plan,
            'invoices': invoices,
            'documents': documents,
            'total_paid': total_paid,
            'remaining_balance': remaining_balance,
            'progress_pct': progress_pct,
            'page_name': 'property_dashboard',
        })
        
        return request.render("construction_erp.portal_property_dashboard", values)

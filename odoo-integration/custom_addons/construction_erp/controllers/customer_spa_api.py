# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import http
# pyrefly: ignore [missing-import]
from odoo.http import request

class CustomerSpaController(http.Controller):

    @http.route('/portal_app', type='http', auth='public', website=False)
    def render_spa(self, **kw):
        return request.render('construction_erp.customer_spa_layout', {})

    @http.route('/api/customer/login', type='json', auth='public')
    def api_login(self, login, password):
        try:
            db = request.env.registry.db_name
            request.session.authenticate(db, login, password)
            user = request.env.user
            return {
                'success': True,
                'uid': user.id,
                'name': user.name,
                'partner_id': user.partner_id.id
            }
        except Exception as e:
            return {'success': False, 'error': "Invalid Username or Password."}

    @http.route('/api/customer/session', type='json', auth='public')
    def api_session(self):
        if request.session.uid:
            user = request.env.user
            return {
                'logged_in': True,
                'name': user.name,
                'partner_id': user.partner_id.id
            }
        return {'logged_in': False}

    @http.route('/api/customer/change_password', type='json', auth='user')
    def api_change_password(self, old_password, new_password, **kw):
        user = request.env.user
        try:
            db = request.env.registry.db_name
            request.session.authenticate(db, user.login, old_password)
            user.sudo().write({'password': new_password})
            return {'success': True}
        except Exception as e:
            return {'error': "Invalid current password."}

    @http.route('/api/customer/update_avatar', type='json', auth='user')
    def api_update_avatar(self, image_base64, **kw):
        user = request.env.user
        try:
            user.partner_id.sudo().write({'image_1920': image_base64})
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/customer/properties', type='json', auth='user')
    def api_properties(self, **kw):
        partner = request.env.user.partner_id
        domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done']),
            ('unit_id', '!=', False)
        ]
        sales = request.env['sale.order'].sudo().search(domain)
        result = []
        for sale in sales:
            result.append({
                'id': sale.id,
                'name': sale.name,
                'project_name': sale.project_id.name,
                'unit_name': sale.unit_id.name if sale.unit_id else '',
                'amount_total': sale.amount_total,
                'currency': sale.currency_id.symbol,
                'state': sale.state
            })
        return {'properties': result}

    @http.route('/api/customer/property_details', type='json', auth='user')
    def api_property_details(self, order_id, **kw):
        sale = request.env['sale.order'].sudo().browse(order_id)
        if not sale.exists() or sale.partner_id != request.env.user.partner_id:
            return {'error': 'Not Found or Access Denied'}

        # Calculate Financials
        invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('project_id', '=', sale.project_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel')
        ])
        
        total_paid = sum(inv.amount_total - inv.amount_residual for inv in invoices.filtered(lambda i: i.state == 'posted'))
        total_amount = sale.amount_total
        remaining_balance = total_amount - total_paid
        progress_pct = round((total_paid / total_amount * 100), 1) if total_amount > 0 else 0

        return {
            'id': sale.id,
            'name': sale.name,
            'project_name': sale.project_id.name,
            'unit_name': sale.unit_id.name if sale.unit_id else '',
            'latitude': sale.project_id.site_latitude,
            'longitude': sale.project_id.site_longitude,
            'total_amount': total_amount,
            'total_paid': total_paid,
            'remaining_balance': remaining_balance,
            'progress_pct': progress_pct,
            'currency': sale.currency_id.symbol,
        }

    @http.route('/api/customer/installments', type='json', auth='user')
    def api_installments(self, order_id, limit=15, offset=0, **kw):
        sale = request.env['sale.order'].sudo().browse(order_id)
        if not sale.exists() or sale.partner_id != request.env.user.partner_id:
            return {'error': 'Not Found'}

        plan = request.env['real_estate.installment.plan'].sudo().search([('sale_id', '=', sale.id)], limit=1)
        if not plan:
            return {'lines': [], 'total': 0}

        lines = plan.line_ids
        total_count = len(lines)
        page_lines = lines[offset:offset+limit]

        result = []
        for line in page_lines:
            status = 'Upcoming'
            if line.invoice_payment_state == 'paid':
                status = 'Paid'
            elif line.invoice_payment_state == 'in_payment':
                status = 'In Payment'
            elif line.is_invoiced:
                status = 'Invoiced'

            result.append({
                'id': line.id,
                'name': line.name,
                'due_date': str(line.due_date),
                'amount': line.amount,
                'status': status,
                'currency': plan.currency_id.symbol
            })

        return {'lines': result, 'total': total_count}

    @http.route('/api/customer/invoices', type='json', auth='user')
    def api_invoices(self, order_id, limit=15, offset=0, **kw):
        sale = request.env['sale.order'].sudo().browse(order_id)
        if not sale.exists() or sale.partner_id != request.env.user.partner_id:
            return {'error': 'Not Found'}

        domain = [
            ('partner_id', '=', request.env.user.partner_id.id),
            ('project_id', '=', sale.project_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '!=', 'cancel')
        ]
        
        invoices = request.env['account.move'].sudo().search(domain, limit=limit, offset=offset)
        total_count = request.env['account.move'].sudo().search_count(domain)

        result = []
        for inv in invoices:
            status = 'Paid' if inv.payment_state in ['paid', 'in_payment'] else 'Pending'
            result.append({
                'id': inv.id,
                'name': inv.name,
                'invoice_date': str(inv.invoice_date),
                'amount_total': inv.amount_total,
                'status': status,
                'currency': inv.currency_id.symbol,
                'url': f'/my/invoices/{inv.id}?access_token={inv.access_token}'
            })

        return {'invoices': result, 'total': total_count}

    @http.route('/api/customer/documents', type='json', auth='user')
    def api_documents(self, order_id, limit=15, offset=0, **kw):
        sale = request.env['sale.order'].sudo().browse(order_id)
        if not sale.exists() or sale.partner_id != request.env.user.partner_id:
            return {'error': 'Not Found'}

        domain = [
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('type', '=', 'binary')
        ]
        docs = request.env['ir.attachment'].sudo().search(domain, limit=limit, offset=offset)
        total_count = request.env['ir.attachment'].sudo().search_count(domain)

        result = []
        for doc in docs:
            result.append({
                'id': doc.id,
                'name': doc.name,
                'mimetype': doc.mimetype,
                'url': f'/web/content/{doc.id}?download=true'
            })
        return {'documents': result, 'total': total_count}

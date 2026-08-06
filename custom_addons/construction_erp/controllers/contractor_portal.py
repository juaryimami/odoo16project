# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ContractorPortal(http.Controller):

    @http.route(['/my/job_orders'], type='http', auth="user", website=True)
    def portal_my_job_orders(self, **kw):
        partner = request.env.user.partner_id
        job_orders = request.env['construction.job.order'].sudo().search([('contractor_id', '=', partner.id)])
        return request.render("construction_erp.portal_my_job_orders", {'job_orders': job_orders})

    @http.route(['/my/job_order/<int:order_id>'], type='http', auth="user", website=True)
    def portal_job_order_detail(self, order_id, **kw):
        partner = request.env.user.partner_id
        job_order = request.env['construction.job.order'].sudo().search([('id', '=', order_id), ('contractor_id', '=', partner.id)], limit=1)
        if not job_order:
            return request.not_found()
        return request.render("construction_erp.portal_job_order_detail", {'job_order': job_order})

    @http.route(['/my/job_order/accept/<int:order_id>'], type='http', auth="user", website=True)
    def portal_job_order_accept(self, order_id, **kw):
        partner = request.env.user.partner_id
        job_order = request.env['construction.job.order'].sudo().search([('id', '=', order_id), ('contractor_id', '=', partner.id)], limit=1)
        if job_order and job_order.state == 'offered':
            job_order.state = 'accepted'
        return request.redirect(f'/my/job_order/{order_id}')

    @http.route(['/my/milestone/request_inspection/<int:milestone_id>'], type='http', auth="user", website=True)
    def portal_milestone_request(self, milestone_id, **kw):
        partner = request.env.user.partner_id
        milestone = request.env['construction.job.milestone'].sudo().search([('id', '=', milestone_id), ('job_order_id.contractor_id', '=', partner.id)], limit=1)
        if milestone and milestone.state == 'pending':
            milestone.state = 'inspection'
            
            # Auto-spawn backend inspection QA Checklist natively tied to the milestone
            request.env['construction.inspection'].sudo().create({
                'name': f"Insp: {milestone.job_order_id.name} - {milestone.name}",
                'milestone_id': milestone.id,
                'state': 'draft'
            })
            
        return request.redirect(f'/my/job_order/{milestone.job_order_id.id}')
    @http.route(['/job_offer/<string:token>/request_payment'], type='http', auth="public", methods=['POST'], website=True)
    def portal_payment_request(self, token, **kw):
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        if not job_order:
            return request.not_found()
            
        claim_pct = float(kw.get('claim_percentage', 0))
        if claim_pct > 0:
            cpr = request.env['construction.cpr'].sudo().create({
                'job_order_id': job_order.id,
                'project_id': job_order.project_id.id,
                'cpr_type': 'progress',
                'current_progress_claim': claim_pct,
                'notes': kw.get('notes'),
                'state': 'draft'
            })
            # Trigger verification logic (which births the inspection)
            cpr.action_verify()
            job_order.message_post(body=f"Contractor submitted a new Payment Request ({claim_pct}%) from the portal.")
            
        return request.redirect(f'/job_offer/{token}')

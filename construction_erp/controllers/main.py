# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request

class JobOrderController(http.Controller):

    @http.route('/job_order/accept/<string:token>', type='http', auth='public', website=True)
    def accept_job_order(self, token, **kwargs):
        """
        Public route to allow contractors to accept a Job Order via a secure token.
        """
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        
        if not job_order:
            return request.render('website.404')
            
        if job_order.state == 'offered':
            job_order.action_accept()
            return request.render('construction_erp.job_order_accepted_page', {
                'job_order': job_order,
            })
        elif job_order.state in ['accepted', 'active', 'completed', 'closed']:
            return request.render('construction_erp.job_order_already_accepted_page', {
                'job_order': job_order,
            })
        else:
            return request.render('website.404')

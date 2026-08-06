# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request

class InspectionPortal(http.Controller):

    @http.route('/inspection/public/<string:token>', type='http', auth="public")
    def public_inspection_form(self, token, **kwargs):
        """ Renders the public inspection grading form. """
        inspection = request.env['construction.inspection'].sudo().search([
            ('access_token', '=', token)
        ], limit=1)

        if not inspection:
            return request.render('construction_erp.portal_inspection_not_found')
        
        if inspection.is_submitted:
            return request.render('construction_erp.portal_inspection_expired', {
                'inspection': inspection
            })

        return request.render('construction_erp.portal_inspection_form', {
            'inspection': inspection,
            'job': inspection.job_order_id,
            'project': inspection.project_id
        })

    @http.route('/inspection/submit', type='http', auth="public", methods=['POST'], csrf=True)
    def public_inspection_submit(self, **post):
        """ Handles the submission of inspection results. """
        token = post.get('token')
        if not token:
            return request.render('construction_erp.portal_inspection_not_found')
            
        inspection = request.env['construction.inspection'].sudo().search([
            ('access_token', '=', token),
            ('is_submitted', '=', False)
        ], limit=1)

        if not inspection:
            return request.render('construction_erp.portal_inspection_expired')

        # Extract line values
        line_vals = {}
        for key, value in post.items():
            if key.startswith('status_'):
                line_id = key.split('_')[1]
                if line_id not in line_vals:
                    line_vals[line_id] = {}
                line_vals[line_id]['status'] = value
            elif key.startswith('notes_'):
                line_id = key.split('_')[1]
                if line_id not in line_vals:
                    line_vals[line_id] = {}
                line_vals[line_id]['notes'] = value
        
        # Add overall notes
        inspection.sudo().write({'notes': post.get('overall_notes')})
        
        # Submit the inspection
        inspection.sudo().action_submit(line_vals=line_vals)

        return request.render('construction_erp.portal_inspection_success', {
            'inspection': inspection
        })

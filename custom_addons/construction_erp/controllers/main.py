# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import base64

class JobOrderController(http.Controller):

    @http.route('/job_offer/<string:token>', type='http', auth='public')
    def job_offer_portal(self, token, **kwargs):
        """
        Public landing page for the Job Order offer.
        """
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        
        if not job_order:
            return request.not_found()
            
        # If accepted, show dashboard (with password check if not in session)
        if job_order.state != 'offered':
            # Check if password is in session
            session_key = f'job_order_{job_order.id}_auth'
            if not request.session.get(session_key):
                return request.render('construction_erp.job_order_password_auth', {
                    'job_order': job_order,
                    'token': token,
                    'error': kwargs.get('error')
                })
            
            # Show Execution Dashboard
            return request.render('construction_erp.job_order_execution_dashboard', {
                'job_order': job_order,
                'token': token,
            })
            
        return request.render('construction_erp.job_order_portal_view', {
            'job_order': job_order,
            'token': token,
        })

    @http.route('/job_offer/<string:token>/authenticate', type='http', auth='public', methods=['POST'], csrf=True)
    def job_order_authenticate(self, token, **post):
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        if not job_order:
            return request.not_found()
            
        password = post.get('password')
        if password == job_order.portal_password:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info("Authentication Success for Job Order %s", job_order.name)
            request.session[f'job_order_{job_order.id}_auth'] = True
            return request.redirect(f'/job_offer/{token}')
        
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning("Authentication Failed for Job Order %s - Password Mismatch", job_order.name)
        return request.redirect(f'/job_offer/{token}?error=invalid_password')

    @http.route('/job_offer/<string:token>/trigger_inspection/<int:milestone_id>', type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_trigger_inspection(self, token, milestone_id, **kw):
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        if not job_order:
            return request.not_found()
            
        # Security: Check session
        if not request.session.get(f'job_order_{job_order.id}_auth'):
            return request.redirect(f'/job_offer/{token}')
            
        milestone = request.env['construction.job.milestone'].sudo().browse(milestone_id)
        if milestone.job_order_id.id != job_order.id:
            return request.not_found()
            
        if milestone.state == 'in_progress':
            # Capture remarks from POST or GET
            remarks = kw.get('remarks', False)
            # Create Inspection via Model Helper
            inspection = milestone.action_create_inspection(remarks=remarks)
            
            # Notify PM via Chatter
            if inspection:
                job_order.message_post(body=_("Phase Completion Reported from Portal for milestone: %s. Quality Gate Created: %s") % (milestone.name, inspection.name))
            
        return request.redirect(f'/job_offer/{token}')

    @http.route('/job_offer/<string:token>/accept', type='http', auth='public', methods=['POST'], csrf=True)
    def job_offer_accept(self, token, **post):
        """
        Endpoint to process job offer acceptance and file uploads.
        """
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        if not job_order or job_order.state != 'offered':
            return request.not_found()

        # 1. Handle File Uploads
        files = request.httprequest.files.getlist('acceptance_papers')
        attachment_ids = []
        for file in files:
            if file.filename:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': file.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(file.read()),
                    'public': True, # Ensure visibility
                    'res_model': 'construction.job.order',
                    'res_id': job_order.id,
                })
                attachment_ids.append(attachment.id)

        # 2. Post Acceptance to Chatter with Contractor identity
        contractor = job_order.contractor_id
        msg = _("Job Offer accepted by %s. Uploaded %d document(s).") % (contractor.name, len(attachment_ids))
        message = job_order.sudo().message_post(
            body=msg, 
            author_id=contractor.id,
            email_from=contractor.email
        )

        # 3. Definitively link attachments to the message via M2M update
        if attachment_ids:
            message.sudo().write({
                'attachment_ids': [(6, 0, attachment_ids)]
            })

        # 4. Finalize Status
        # We NO LONGER expire the token, as it upgrades to a passworded execution link
        job_order.sudo().action_accept()

        return request.render('construction_erp.job_order_accepted_page', {
            'job_order': job_order,
        })

    @http.route('/job_offer/<string:token>/reject', type='http', auth='public', methods=['POST'], csrf=True)
    def job_offer_reject(self, token, **post):
        """
        Endpoint to process job offer rejection.
        """
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        if not job_order or job_order.state != 'offered':
            return request.not_found()

        reason = post.get('rejection_reason', 'No specific reason provided.')
        job_order.sudo().write({
            'state': 'draft',
            'rejection_reason': reason,
            'access_token': False  # Token expires after use
        })
        
        contractor = job_order.contractor_id
        msg = _("<b>Offer Rejected by %s</b><br/>Reason: %s") % (contractor.name, reason)
        job_order.sudo().message_post(
            body=msg,
            author_id=contractor.id,
            email_from=contractor.email
        )

        return request.render('construction_erp.job_order_rejected_page', {
            'job_order': job_order,
        })

    @http.route('/job_offer/<string:token>/change_password', type='http', auth='public', methods=['POST'], csrf=True)
    def job_order_change_password(self, token, **post):
        """
        Allows contractor to change their portal access password.
        """
        job_order = request.env['construction.job.order'].sudo().search([('access_token', '=', token)], limit=1)
        if not job_order:
            return request.not_found()
            
        # Security: Check session
        if not request.session.get(f'job_order_{job_order.id}_auth'):
            return request.redirect(f'/job_offer/{token}')
            
        old_password = post.get('old_password')
        new_password = post.get('new_password')
        confirm_password = post.get('confirm_password')
        
        if old_password != job_order.portal_password:
            return request.redirect(f'/job_offer/{token}?error=old_password_invalid')
            
        if not new_password or new_password != confirm_password:
            return request.redirect(f'/job_offer/{token}?error=password_mismatch')
            
        job_order.sudo().write({'portal_password': new_password})
        job_order.message_post(body=_("<b>Security Update:</b> Contractor successfully changed their portal access password."))
        
        return request.redirect(f'/job_offer/{token}?success=password_changed')

    @http.route('/construction/estimate_template', type='http', auth='user')
    def download_estimate_template(self, **kwargs):
        """
        Generates and downloads a sample Excel template for importing cost estimation lines.
        """
        import io
        try:
            import xlsxwriter
        except ImportError:
            xlsxwriter = None
            
        filename = "estimate_import_template.xlsx"
        
        if xlsxwriter:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Sample Estimate Template')
            
            # Format styles
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4e73df',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            guide_format = workbook.add_format({
                'italic': True,
                'font_color': '#5a5c69',
                'bg_color': '#f8f9fc',
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            data_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            number_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '#,##0.00'
            })
            
            qty_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '#,##0'
            })

            # Headers
            headers = ['Product', 'Category', 'Quantity', 'Unit Cost']
            worksheet.set_row(0, 30)
            for col_idx, header in enumerate(headers):
                worksheet.write(0, col_idx, header, header_format)
                
            # Sample Data Rows
            samples = [
                ('Portland Cement (Grade 53)', 'Material', 500, 8.50),
                ('Excavator Hire (Volvo EC220)', 'Equipment', 5, 250.00),
                ('Site Supervisor Labor', 'Labor', 160, 25.00),
                ('Concrete Mixer Fleet Transport', 'Fleet', 12, 120.00),
                ('Safety Signage and Admin', 'Overhead', 1, 850.00)
            ]
            
            for row_idx, sample in enumerate(samples, start=1):
                worksheet.set_row(row_idx, 20)
                worksheet.write(row_idx, 0, sample[0], data_format)
                worksheet.write(row_idx, 1, sample[1], data_format)
                worksheet.write(row_idx, 2, sample[2], qty_format)
                worksheet.write(row_idx, 3, sample[3], number_format)
                
            # Add guidance text
            worksheet.set_row(7, 25)
            worksheet.merge_range('A8:D8', 'GUIDE FOR EXCEL IMPORT PREPARATION', workbook.add_format({'bold': True, 'bg_color': '#eaecf0', 'align': 'center'}))
            
            guidelines = [
                ('Product', 'Name of product (e.g. Portland Cement). If the product does not exist, it will be automatically created.'),
                ('Category', 'Allowed types: "Material", "Equipment", "Labor", "Fleet" (or "Vehicle"), "Overhead" (or "Admin").'),
                ('Quantity', 'Numeric value representing the quantity of the item estimated for this phase.'),
                ('Unit Cost', 'Numeric value representing the unit price or cost of the item.')
            ]
            
            for idx, guide in enumerate(guidelines, start=8):
                worksheet.set_row(idx, 20)
                worksheet.write(idx, 0, guide[0], workbook.add_format({'bold': True, 'border': 1}))
                worksheet.merge_range(idx, 1, idx, 3, guide[1], guide_format)
                
            # Column widths
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 12)
            worksheet.set_column('D:D', 15)
            
            workbook.close()
            output.seek(0)
            excel_data = output.read()
            
            return request.make_response(
                excel_data,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', f'attachment; filename={filename}')
                ]
            )
        else:
            # Fallback to CSV if xlsxwriter is not installed
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Product', 'Category', 'Quantity', 'Unit Cost'])
            writer.writerow(['Portland Cement (Grade 53)', 'Material', '500', '8.50'])
            writer.writerow(['Excavator Hire (Volvo EC220)', 'Equipment', '5', '250.00'])
            writer.writerow(['Site Supervisor Labor', 'Labor', '160', '25.00'])
            writer.writerow(['Concrete Mixer Fleet Transport', 'Fleet', '12', '120.00'])
            writer.writerow(['Safety Signage and Admin', 'Overhead', '1', '850.00'])
            
            csv_data = output.getvalue().encode('utf-8')
            filename = "estimate_import_template.csv"
            return request.make_response(
                csv_data,
                headers=[
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', f'attachment; filename={filename}')
                ]
            )

    @http.route('/construction/checklist_template', type='http', auth='user')
    def download_checklist_template(self, **kwargs):
        """
        Generates and downloads a sample Excel template for importing checklist template items.
        """
        import io
        try:
            import xlsxwriter
        except ImportError:
            xlsxwriter = None
            
        filename = "checklist_import_template.xlsx"
        
        if xlsxwriter:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Checklist Template')
            
            # Format styles
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4e73df',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            guide_format = workbook.add_format({
                'italic': True,
                'font_color': '#5a5c69',
                'bg_color': '#f8f9fc',
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            data_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            seq_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'num_format': '#,##0'
            })
            
            bool_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            # Headers
            headers = ['Sequence', 'Item Name', 'Mandatory']
            worksheet.set_row(0, 30)
            for col_idx, header in enumerate(headers):
                worksheet.write(0, col_idx, header, header_format)
                
            # Sample Data Rows
            samples = [
                (10, 'Verify concrete compressive strength (28-day cure)', 'Yes'),
                (20, 'Perform slump test on arrival of transit mixer', 'Yes'),
                (30, 'Inspect reinforcement steel spacing and clear cover', 'Yes'),
                (40, 'Check formwork alignment and verticality', 'Yes'),
                (50, 'Take site photos of reinforcement before pour', 'No')
            ]
            
            for row_idx, sample in enumerate(samples, start=1):
                worksheet.set_row(row_idx, 20)
                worksheet.write(row_idx, 0, sample[0], seq_format)
                worksheet.write(row_idx, 1, sample[1], data_format)
                worksheet.write(row_idx, 2, sample[2], bool_format)
                
            # Add guidance text
            worksheet.set_row(7, 25)
            worksheet.merge_range('A8:C8', 'GUIDE FOR CHECKLIST IMPORT PREPARATION', workbook.add_format({'bold': True, 'bg_color': '#eaecf0', 'align': 'center'}))
            
            guidelines = [
                ('Sequence', 'Numeric value for sorting order (e.g. 10, 20, 30). Defaults to 10 if not provided.'),
                ('Item Name', 'Descriptive checklist requirement/check item (Required).'),
                ('Mandatory', 'Either "Yes" / "True" / "1" if mandatory, or "No" / "False" / "0" if optional.')
            ]
            
            for idx, guide in enumerate(guidelines, start=8):
                worksheet.set_row(idx, 20)
                worksheet.write(idx, 0, guide[0], workbook.add_format({'bold': True, 'border': 1}))
                worksheet.merge_range(idx, 1, idx, 2, guide[1], guide_format)
                
            # Column widths
            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 55)
            worksheet.set_column('C:C', 12)
            
            workbook.close()
            output.seek(0)
            excel_data = output.read()
            
            return request.make_response(
                excel_data,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', f'attachment; filename={filename}')
                ]
            )
        else:
            # Fallback to CSV if xlsxwriter is not installed
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Sequence', 'Item Name', 'Mandatory'])
            writer.writerow(['10', 'Verify concrete compressive strength (28-day cure)', 'Yes'])
            writer.writerow(['20', 'Perform slump test on arrival of transit mixer', 'Yes'])
            writer.writerow(['30', 'Inspect reinforcement steel spacing and clear cover', 'Yes'])
            writer.writerow(['40', 'Check formwork alignment and verticality', 'Yes'])
            writer.writerow(['50', 'Take site photos of reinforcement before pour', 'No'])
            
            csv_data = output.getvalue().encode('utf-8')
            filename = "checklist_import_template.csv"
            return request.make_response(
                csv_data,
                headers=[
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', f'attachment; filename={filename}')
                ]
            )

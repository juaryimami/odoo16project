from odoo import http
from odoo.http import request
import json

class RecruitmentController(http.Controller):

    @http.route('/recruitment/application', type='http', auth='public', website=True)
    def recruitment_application(self, **kwargs):
        degrees = request.env['hr.recruitment.degree'].sudo().search([])  # Fetch all degrees
        return request.render('recruitment.recruitment_application_form', {
            'degrees': degrees
        })

    @http.route('/recruitment/submit', type='http', auth='public', website=True, csrf=True)
    def recruitment_submit(self, **kwargs):
        if request.httprequest.method == 'POST':
            name = kwargs.get('name')
            email = kwargs.get('email')
            phone = kwargs.get('phone')
            job_position_id = kwargs.get('job_position_id')
            resume = kwargs.get('resume')
            cover_letter = kwargs.get('cover_letter')
            date_applied = kwargs.get('date_applied')
            gender = kwargs.get('gender')
            reason_to_apply = kwargs.get('reason_to_apply')

            # Create the application record
            application = request.env['recruitment.application'].sudo().create({
                'name': name,
                'email': email,
                'phone': phone,
                'job_position_id': job_position_id,
                'resume': resume,
                'cover_letter': cover_letter,
                'date_applied': date_applied,
                'gender': gender,
                'reason_to_apply': reason_to_apply
            })

            # Handle education background from local storage
            educations = request.httprequest.form.get('educations')
            if educations:
                educations = json.loads(educations)
                for education in educations:
                    request.env['recruitment.education'].sudo().create({
                        'school_name': education['school_name'],
                        'degree_id': int(education['degree_id']),
                        'specialization': education['specialization'],
                        'start_date': education['start_date'],
                        'end_date': education['end_date'],
                        'description': education['description'],
                        'application_id': application.id
                    })

            # Clear local storage after saving
            return """
            <script>
                localStorage.removeItem('educations');
                window.location.href = '/recruitment/submit_success';
            </script>
            """

        return request.redirect('/recruitment/application')  # Redirect to application page if method is not POST

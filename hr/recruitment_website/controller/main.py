from odoo import http
import base64
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from datetime import datetime

import json
class SariaWebsite(http.Controller):

    @http.route('/jobs', type='http', auth="public", website=True)
    def index(self):

        jobs = http.request.env['recruitment.jobs'].sudo().search([('state', '=', 'post')])
        department_ids = jobs.mapped('department_id').ids
        departments = http.request.env['hr.department'].sudo().search([('id', 'in', department_ids)])
        contracts_ids = jobs.mapped('employment_type').ids
        contracts = request.env['hr.contract.type'].search([('id', 'in', contracts_ids)])
        return http.request.render('recruitment_website.job_list',{
            'departments': departments,
            'jobs': jobs,
            'contracts': contracts
        })

    # @http.route('/job_list/', auth='public', website=True)
    # def index(self):
    #     print('print')

    @http.route('''/job/detail/<model("recruitment.jobs"):job>''', type='http', auth="public", website=True)
    def job_detail(self,job,**kwargs):
        # env = request.env(context=dict(request.env.context))
        jobdetail = http.request.env['recruitment.jobs'].sudo().search(['&',('id', '=', job.id),('state','=','post')])
        jobs = http.request.env['recruitment.jobs'].sudo().search([('state', '=', 'post')])
        department_ids = jobs.mapped('department_id').ids
        departments = http.request.env['hr.department'].sudo().search([('id', 'in', department_ids)])
        contracts_ids = jobdetail.mapped('employment_type').ids
        contracts = request.env['hr.contract.type'].search([('id', 'in', contracts_ids)])

        return http.request.render('recruitment_website.job_detail', {
            'job': jobdetail,
            'contracts': contracts,
            'departments': departments
        })

    # @http.route('/job_list/detail/', auth='public', website=True)
    # def job_detail_list(self):
    #
    #     return http.request.render('recruitment_website.detail_list',{})
    # Job list by department

    @http.route('/category/<model("hr.department"):id>/', auth='public', website=True)
    def job_detail_department(self, id):
        jobs = http.request.env['recruitment.jobs'].sudo().search(['&',('department_id','=',id.id),('state','=','post')])
        jobss = http.request.env['recruitment.jobs'].sudo().search([('state', '=', 'post')])
        department_ids = jobss.mapped('department_id').ids
        departments = http.request.env['hr.department'].sudo().search([('id', 'in', department_ids)])
        contracts_ids = jobss.mapped('employment_type').ids
        contracts = request.env['hr.contract.type'].search([('id', 'in', contracts_ids)])
        return http.request.render('recruitment_website.job_list_by_department', {

            'departments': departments,
            'bydepartment': jobs,
            'department_id':id.name,
            'contracts':contracts
        })

    @http.route('/employment/<model("hr.contract.type"):id>/', auth='public', website=True)
    def job_detail_employment(self, id):
        jobs = http.request.env['recruitment.jobs'].sudo().search(['&',('employment_type', '=', id.id),('state','=','post')])
        jobss = http.request.env['recruitment.jobs'].sudo().search([('state', '=', 'post')])
        department_ids = jobss.mapped('department_id').ids
        departments = http.request.env['hr.department'].sudo().search([('id', 'in', department_ids)])
        contracts_ids = jobss.mapped('employment_type').ids
        contracts = request.env['hr.contract.type'].search([('id', 'in', contracts_ids)])
        return http.request.render('recruitment_website.job_list_employment_type', {

            'departments': departments,
            'byemployment': jobs,
            'emptype_id': id.name,
            'contracts': contracts
        })

    @http.route('/apply/default/', auth='public', website=True)
    def default_apply(self):
        job=http.request.env['recruitment.jobs'].sudo().search([('name','=','none')],limit=1)
        if not job:
            job = request.env['recruitment.jobs'].sudo().create({
                'name': "none",
                'deadline_date':datetime.now()
            })
        university = http.request.env['applicant.university'].sudo().search([])
        degress = http.request.env['hr.recruitment.degree'].sudo().search([])
        address = http.request.env['res.country'].sudo().search([])

        currencies = http.request.env['res.currency'].sudo().search([])
        industries = http.request.env['applicant.industry'].sudo().search([])

        reasons = http.request.env['reason.seeking'].sudo().search([])
        language_lists = http.request.env['language.skill'].sudo().search([])
        salaries = http.request.env['expected.salary'].sudo().search([])
        benefits = http.request.env['expected.benefit'].sudo().search([])
        experiences = http.request.env['total.experience'].sudo().search([])
        availabilities = http.request.env['applicant.availability'].sudo().search([])
        # print('printing', languages)
        # for add in address:
        #     state = http.request.env['res.country.state'].search([('address_id', '=', add.id)])

        return http.request.render('recruitment_website.job_apply', {
            'univers': university,
            'job': job[0],
            'degrees': degress,
            'address': address,
            'currencies': currencies,
            'industries': industries,
            'reasons': reasons,
            'language_list': language_lists,
            'salaries': salaries,
            'benefits': benefits,
            'experiences': experiences,
            'availabilities': availabilities

        })

    @http.route('/apply/<model("recruitment.jobs"):job>/', auth='public', website=True)
    def apply(self, job):
        university = http.request.env['applicant.university'].sudo().search([])
        degress = http.request.env['hr.recruitment.degree'].sudo().search([])
        address = http.request.env['res.country'].sudo().search([])

        currencies = http.request.env['res.currency'].sudo().search([])
        industries = http.request.env['applicant.industry'].sudo().search([])

        reasons = http.request.env['reason.seeking'].sudo().search([])
        language_lists = http.request.env['language.skill'].sudo().search([])
        salaries = http.request.env['expected.salary'].sudo().search([])
        benefits = http.request.env['expected.benefit'].sudo().search([])
        experiences = http.request.env['total.experience'].sudo().search([])
        availabilities = http.request.env['applicant.availability'].sudo().search([])
        # print('printing', languages)
        # for add in address:
        #     state = http.request.env['res.country.state'].search([('address_id', '=', add.id)])

        return http.request.render('recruitment_website.job_apply', {
            'univers': university,
            'job': job,
            'degrees':degress,
            'address': address,
            'currencies': currencies,
            'industries': industries,
            'reasons': reasons,
            'language_list': language_lists,
            'salaries':salaries,
            'benefits':benefits,
            'experiences': experiences,
            'availabilities':availabilities

        })

    @http.route('/apply/job_position', type="http", auth='public', website=True)
    def apply_create(self, **kw):
        # Read file and experiences/educations
        file = kw.get('att')
        file_attachment = file.read()
        # Validate benefits
        benefit_ids = request.httprequest.form.getlist('expected_benefit')
        if benefit_ids:
            try:
                benefit_ids = [int(id) for id in benefit_ids]
            except ValueError:
                benefit_ids=False

        # Get form values
        job = kw.get('job_name')
        applicant = kw.get('applicant_name')
        subject = f"{applicant} Application for {job}"
        try:
            request.env['hr.applicant'].sudo().create({
                'partner_phone': kw.get('phone'),
                'phone_two': kw.get('phone_two'),
                'email_from': kw.get('email'),
                'recruitment_job_id': kw.get('recruitment_job_id'),
                'gender': kw.get('gender'),
                'partner_name': applicant,
                'availability_id': kw.get('availability'),
                'other_language': kw.get('other_language'),
                'name': subject,
                'year_experience': kw.get('experience_year'),
                'applicant_address': kw.get('living_address'),
                'expected_salary': kw.get('expected_salary'),
                'reason': kw.get('reason'),
                'description': kw.get('application_summary'),
                'hourly_rate_amount': kw.get('hourly_rate_amount'),
                'resume': base64.b64encode(file_attachment) if file_attachment else False,
            })
        except Exception as e:
            return http.request.render('recruitment_website.error', {'error': str(e)})

        return http.request.render('recruitment_website.thanks', {})


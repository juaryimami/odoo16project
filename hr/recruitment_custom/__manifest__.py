{
    'name': 'Recruitment Custom',
    'version': '1.1',
    'summary': 'Saria Module',
    'description': """Saria""",
    'category': '',
    'website': '',
    'depends': [
        'base',
        'base_setup',
        'hr_recruitment',
        'employee_interview',
        'recruitment_jobs',
        'recruitment_website',
        # 'ssq_recruitment_applicant_experience'
    ],

    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'views/resume_screening.xml',
        'views/experience_views.xml',
        # 'views/education_views.xml',
        'views/applicant_saria.xml',
        'views/university_applicant.xml',
        'views/applicant_industry.xml',
        'views/reason_seeking.xml',
        'views/language_skill.xml',
        'views/expected_salary.xml',
        'views/expected_benefit.xml',
        'views/total_experience.xml',
        'views/reason_drop.xml',
        'views/reason_reject.xml',
        # 'views/hide_filter.xml',
        'views/applicant_availability.xml',
        'views/update_stage_form_view.xml',
        'views/update_applicant_company_view.xml'

    ],
    'assets': {},
    'installable': True,
    'application': True,
}

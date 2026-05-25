{
    'name': 'Recruitment Request Management',

    'summary': 'Manage recruitment requests ',
    'description': 'This module allows you to manage recruitment requests within  company.',
    'author': 'Tamrat',
    'category': 'Human Resources',
    'depends': ['base', 'hr','hr_recruitment'],
    'data': [
        'views/request_recruitment.xml',
        'views/education_level_view.xml',
        'views/education_type_view.xml',
        'views/experience_level_view.xml',
        'views/experience_type_form.xml',
        'security/ir.model.access.csv',

        'data/data.xml',


        'views/hr_applicant_views.xml',



    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

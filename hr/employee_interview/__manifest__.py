# -*- coding: utf-8 -*-

{
    'name': 'Employee Interview',
    'version': '17.0',
    'category': 'HR',
    'summary': """

    """,
    'description': """Employee interview form""",
    'author': 'Tekle Yitayew',
    'company': 'Ashewa Technology Solutions',
    'depends': ['base', 'hr','hr_recruitment'],
    'data': [
        'security/ir.model.access.csv',
        'security/users_grups.xml',
        'data/data.xml',
        'view/blue_interview.xml',
        'view/employee_interview.xml',
        'view/interview_grade.xml',
        'view/interview_question.xml',
        'view/blue_question.xml'

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
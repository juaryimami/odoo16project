{
    'name': 'Employee Promotion',
    'version': '17.0.0.1',
    
    'category': 'Human Resources',
    'summary': 'Track employee promotions',
    'author': 'Tamrat',

    'depends': ['base', 'hr','history_employee'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_promotion.xml',
        'views/hr_employee_views.xml',
        'views/employee_demotion.xml',

    ],
    'installable': True,
    'application': True,
}

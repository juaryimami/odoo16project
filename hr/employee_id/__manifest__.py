{
    'name': 'Employee Reference Number',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Add sequential reference number to employees',
    'depends': ['hr'],
    'data': [
        'data/ir_sequence_data.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
}

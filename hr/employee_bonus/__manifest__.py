{
    'name': 'Employee Bonus',
    'version': '17.0.0.1',
    'summary': 'Employee Bonus',
    'description': """Employee Bonus""",
    'category': 'Human Resource',
    'website': '',
    'depends': [
        'hr',
        'base',
        'base_setup',
        'om_hr_payroll'
    ],

    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        # 'views/hr_payslip.xml',
        'views/employee_bonus.xml',
    ],
    'assets': {},
    'installable': True,
    'application': False,
}

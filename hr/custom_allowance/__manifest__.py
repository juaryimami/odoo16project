{
    'name': 'Custom allowance',
    'version': '17.0.0.0',
    'summary': 'Adds additional fields to hr.contract model for allowances and payments.',
    'category': 'Human Resources',
    'author': 'Tamrat',
    'license': 'AGPL-3',


    'depends': ['base', 'hr_contract'],

    'data': [
        'views/custom_allowance.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}

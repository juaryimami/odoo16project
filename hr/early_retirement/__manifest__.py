{
    'name': 'Retirement Request',
    'version': '17.0.1.1',
    'summary': 'email: tekleyitayew12@gmail.com, Phone: +251 96913925',
    'description': """Early retirement request form""",

    'category': 'Human Resource ',
    'website': '',
    'depends': [
        'base',
        'base_setup',
        'hr',
        'de_hr_workspace'
    ],
    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'security/early_retirement_group.xml',
        'data/early_retirement_notification.xml',
        'views/early_retirement.xml',
    ],
    'assets': {},
    'installable': True,
    'application': False,
    'images': ['static/description/banner.jpg'],

}

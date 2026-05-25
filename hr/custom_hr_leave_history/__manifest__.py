{
    'name': 'Custom Employee Leave Balance',
    'version': '1.0',
    'summary': 'Custom Employee Leave Balance',
    'sequence': 120,
    'description': """
        Custom Employee Leave Balancee.
    """,
    'author': 'Yayal Abayneh',
    'depends': ['base','hr','hr_holidays'],
     'data': [
         'security/ir.model.access.csv',
         'views/custom_hr_leave_history_view.xml',
         'views/custom_hr_leave_view.xml',
     ],
    'assets': {
        'web._assets_primary_variables': [
        ],
        'web.assets_backend': [
        ],
    },
    'installable': True,
    'auto_install': False,
}
           

        

{
    'name': "Recruitment Job List",
    'version': "17.0",
    'summary': """Job List for recruitment""",
    'description': """holds all hr module features""",
    'author': "Tekle Yitayew",
    'company': "Ashewa Technology Solutions",
    'maintainer': "Tekle Yitayew",
    'website': "https://www.ashewa.com",
    'category': 'HR',
    'depends': ['base',
                'hr',
                'hr_recruitment'],
    'data': [
        'security/ir.model.access.csv',
        'views/job_list.xml',
        'views/job_status.xml',
        'views/job_category.xml'


    ],

    'license': "AGPL-3",
    'installable': True,
    'application': False,
    # 'icon': 'static/description/icon/icon.png',
}

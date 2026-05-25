{
    'name': 'Recruitment Website',
    'version': '1.1',
    'summary': 'Recruitment Website',
    'description': """Saria""",
    'category': '',
    'website': '',
    'depends': [
        'base',
        'base_setup',
        'website'
    ],

    'license': 'LGPL-3',

    'data': [


        'views/template.xml',
        # 'views/template2.xml',
        'views/website_menu.xml',
        'views/menu.xml',
        'views/sidebar.xml',


    ],
    'assets': {
        'web.assets_frontend': [
            'recruitment_website/static/src/scss/portal.scss'
            'recruitment_website/static/src/js/custom_storage.js',
        ],
    },
    'installable': True,
    'application': True,
}

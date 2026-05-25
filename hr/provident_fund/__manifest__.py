
{
    'name': "Ethiopian provident fund",
    'version': "17.0",
    'summary': """Deposit withdraw employee's provident fund easily""",
    'description': """Deposit Employee's PF from Monthly payroll and ask for withdrwal of total balance in percent""",
    'author': "Tekle Yitayew",
    'company': "Odoo Ethiopia",
    'category': 'Human resource',
    'depends': ['base_setup','hr','om_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'security/users_grups.xml',
        'data/mail_template_data.xml',
        'data/activity.xml',
        'report/provident_fund.xml',
        'views/res_config/res_config_settings_view.xml',
        'views/provident_fund/provident_fund.xml',
        'views/provident_fund/balance.xml',
        'views/provident_fund/deposits.xml',
        'views/pad_custom_header_layout.xml'
    ],

    'license': "AGPL-3",
    'installable': True,
    'application': True,
    'images': ['static/description/banner.jpg'],
}

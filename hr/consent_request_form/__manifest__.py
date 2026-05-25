# __manifest__.py

{
    'name': 'Consent Request Form',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Module for managing consent request forms',
    'author': 'Your Name',
    'depends': ['base', 'hr','om_hr_payroll', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'security/consent_form_user_group.xml',
        'views/consent_request_form_views.xml',
        'data/pf_salary_rule.xml',
        'reports/consent_report.xml',
        'reports/consent_request_report.xml',],
    'installable': True,
    'auto_install': False,
}

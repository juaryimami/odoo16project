{
    'name': 'Orbit HR Leave Management',
    'version': '1.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Custom Leave Management based on Ethiopian Labour Law',
    'description': """
Orbit HR Leave Management

- Enforces Probation restrictions on leave.
- Short Sick Leave limits (Max 2 undocumented days/year).
- Unpaid Leave limits (Max 2 requests/year).
- Annual Leave Expiry (after 2 years).
- Sick Leave Tiers (100% for 30 days, 50% next 60 days, Unpaid thereafter).
- Document requirements for specific leave types.
    """,
    'author': 'Orbit Health',
    'depends': ['hr', 'hr_holidays', 'hr_contract', 'hr_payroll_community', 'account', 'hr_holidays_attendance'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_payslip_run_views.xml',
        'views/hr_payroll_account_views.xml',
        'views/report_payslip_templates_inherit.xml',
        'wizard/hr_payslip_employees_views.xml',
        'data/ir_cron.xml',
        'data/hr_payroll_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-
{
    'name': 'Ethiopian Payroll Localization',
    'version': '16.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Ethiopian Payroll Localization, Tax Brackets (2025), Pension Rules',
    'description': """
Ethiopian Payroll Localization
==============================
This module provides Ethiopian payroll rules, structures, and configurations.

Features:
- Ethiopian Tax Brackets (Income Tax Amendment Proclamation No. 1395/2025)
- Employee and Employer Pension Deductions
- Payroll Categories for Allowances and Gross/Net
- Customized Ethiopian Payslip Report
- Custom Contract Allowance Fields
    """,
    'author': 'Orbit Health',
    'depends': ['hr_payroll_community', 'hr_contract'],
    'data': [
        'data/payroll_categories.xml',
        'data/salary_rules.xml',
        'data/salary_structure.xml',
        'report/ethiopian_payslip.xml',
        'views/hr_contract_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

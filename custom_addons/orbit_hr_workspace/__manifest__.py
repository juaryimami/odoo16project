# -*- coding: utf-8 -*-
{
    'name': "Advanced Employee Workspace",
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'summary': """
        Consolidated Advanced Employee Self-Service Workspace
        """,
    'description': """
        A fully integrated and advanced self-service workspace for employees.
        Includes modules for Profile, Attendance, Time Off, Expenses, Projects, Overtime, and Payslips.
    """,
    'author': 'Antigravity',
    'depends': [
        'base',
        'hr',
        'hr_contract',
        'hr_attendance',
        'hr_holidays',
        'project',
        'hr_expense',
        'ohrms_overtime',
        'hr_payroll_community',
        'hr_skills'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/attendance_generator_wizard_views.xml',
        'views/attendance_approve_wizard_views.xml',
        'views/attendance_absent_wizard_views.xml',
        'views/workspace_menu.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_holidays_views.xml',
        'views/project_views.xml',
        'views/hr_expense_views.xml',
        'views/hr_overtime_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'orbit_hr_workspace/static/src/js/attendance_list_controller.js',
            'orbit_hr_workspace/static/src/xml/attendance_list_buttons.xml',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}

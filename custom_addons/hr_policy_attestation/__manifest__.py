# -*- coding: utf-8 -*-
{
    'name': 'HR Policy Management and Attestation',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage corporate policies and track employee attestations',
    'description': """
        Policy Management and Attestation Module
        ========================================
        This module provides an independent app to manage HR policies, documents, and track
        employee attestations with strict version control and digital fingerprinting.
    """,
    'author': 'Orbit Health',
    'website': 'https://www.orbithealth.co',
    'depends': ['hr', 'mail', 'orbit_hr_workspace'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/hr_policy_publish_wizard_views.xml',
        'views/hr_policy_template_views.xml',
        'views/hr_policy_dashboard_views.xml',
        'views/hr_policy_employee_views.xml',
        'views/hr_policy_menus.xml',
        'data/mail_template_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_policy_attestation/static/src/scss/policy_dashboard.scss',
            'hr_policy_attestation/static/src/xml/policy_dashboard_templates.xml',
            'hr_policy_attestation/static/src/js/policy_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-
{
    'name': "Time Off Workspace - Self Service",
    'summary': """
        Self-Service Time Off and Holiday Requests
    """,
    'description': """
        The Self-Service Time Off and Holiday Requests sub-module within the employee workspace in Odoo allows users to autonomously request time off or holidays. Employees can conveniently submit requests for annual leave, sick leave, or any other types of time off. Additionally, they can review the status of their requests and access a comprehensive history of their time-off approvals. This feature puts control in the hands of employees, simplifying the process of managing time off and ensuring transparency in leave management within the organization.
    """,
    'author': 'Dynexcel',
    'website': 'https://www.dynexcel.com',
    'version': '0.1',
    'category': 'Human Resources',

    # any module necessary for this one to work correctly
    'depends': ['hr','de_hr_workspace','hr_holidays'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/leave_users_group.xml',
        'data/leave_request_notification.xml',
        'views/hr_holidays_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}

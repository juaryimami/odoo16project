# -*- coding: utf-8 -*-
{
    'name': "Employee Project and Task Management Workspace - Self Service",
    'summary': """
        Self-Service Project and Task Management
    """,
    'description': """
        The Self-Service Project and Task Management sub-module within the employee workspace in Odoo gives users the ability to proactively manage their projects and tasks. Employees can effortlessly create, assign, and track tasks related to their projects. They can also monitor project progress and timelines, enhancing collaboration and productivity. This feature empowers employees to take ownership of their work, simplifying project management and fostering transparency in task assignments and project outcomes within the organization.
    """,
    'author': 'Dynexcel',
    'website': 'https://www.dynexcel.com',
    'version': '0.1',
    'category': 'Human Resources',

    # any module necessary for this one to work correctly
    'depends': ['de_hr_workspace','project'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/project_views.xml',
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

# -*- coding: utf-8 -*-
{
    'name': "Employee Attendance - Self Service",
    'summary': """
        Self-Service Attendance Management
    """,
    'description': """
        The Self-Service Attendance Management sub-module within the employee workspace in Odoo empowers users to conveniently mark their own attendance and review their attendance records. Employees can effortlessly log manual attendance entries, making it easy to account for irregular hours or remote work. Furthermore, they can access a detailed attendance history, providing transparency and control over their attendance data. This feature enhances user autonomy and streamlines attendance tracking within the organization.
    """,
    'author': 'Dynexcel',
    'website': 'https://www.dynexcel.com',
    'version': '0.1',
    'category': 'Human Resources',

    'depends': ['de_hr_workspace','hr_attendance'],

    # always loaded
    'data': [
        'security/security.xml',
        # 'security/ir.model.access.csv',
        'views/hr_attendance_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'OPL-1',
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}

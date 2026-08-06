# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Auto Sequence on Project Task',
    'version': '16.0.0.3',
    'category':'Project',
    'license':'OPL-1',
    'summary': 'This app help to create automatic sequence of project task',
    'description':"""Auto Sequence on Project Task, Auto Sequence Task, Project Task Sequance, Auto numbering on task, Task numbering, Auto generate sequnce on task""", 
    'author': 'BROWSEINFO',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_project_task_sequence&version=16&edition=Community',
    'depends':['project'],
    'data':[
        'data/ir_sequence_data.xml',
        'views/project_task.xml',
        ],
    'installable': True,
    'auto_install': False,
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_project_task_sequence&version=16&edition=Community',
    "images":["static/description/Banner.gif"],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

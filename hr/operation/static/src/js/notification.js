odoo.define('edomias_agent.notification', function (require) {
    'use strict';

     var core = require('web.core');
    var bus = require('bus.bus');
    var session = require('web.session');
    var Notification = require('web.Notification');

    var QWeb = core.qweb;

    bus.bus.on('notification', function (message) {
        var title = message[1].title;
        var body = message[1].message;
        new Notification({
            title: title,
            message: body,
            type: 'info'
        }).appendTo($('body'));
    });
});
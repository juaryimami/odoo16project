/** @odoo-module **/

import { Notification } from '@web/core/notification/notification';

const { Component } = owl;

export class NotificationHandler extends Component {
    static template = 'NotificationHandler';

    constructor() {
        super(...arguments);
        this.notifications = [];
        this._initialize();
    }

    _initialize() {
        this.env.bus.on('notification', this, this._onNotification);
    }

    _onNotification(notification) {
        this.notifications.push(notification);
        this.render();
    }
}

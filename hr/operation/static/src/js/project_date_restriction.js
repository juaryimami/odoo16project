odoo.define('edomias_agent.project_date_restriction', function (require) {
    "use strict";


    var core = require('web.core');
    var form_common = require('web.form_common');
    var datetime = require('web.datetime');
    var QWeb = core.qweb;

    form_common.FormView.include({
        render_view: function () {
            this._super.apply(this, arguments);

            var self = this;
            // Ensure that the date picker elements are available
            this.$('input[type="date"]').each(function () {
                var $input = $(this);
                // Get current date in YYYY-MM-DD format
                var today = new Date().toISOString().split('T')[0];
                $input.attr('min', today);
            });
        }
    });
});

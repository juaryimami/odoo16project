odoo.define("nona.redirectToProduct", function (require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");
    ListRenderer.include({
        _renderRow: function (record) {
            let row = this._super(record);
            var self = this;
            if (record.model == "custom.hr.payroll.report") {
                row.addClass('o_list_no_open');
                // add click event
                console.log("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii");
                row.bind({
                    click: function (ev) {
                        ev.preventDefault();
                        ev.stopPropagation();
                        self.do_action({
                            type: "ir.actions.act_window",
                            res_model: "hr.payslip",
                            res_id: record.data.payslip_id.id,
                            views: [[false, "form"]],
                            target: "target",
                            context: record.context || {},
                        });
                    }
                });
            }
            return row
        },
    });
});
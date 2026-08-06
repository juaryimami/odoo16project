/** @odoo-module */

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { useService } from "@web/core/utils/hooks";

export class AttendanceListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    async onGenerateAttendances() {
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'orbit.attendance.generator.wizard',
            views: [[false, 'form']],
            target: 'new',
            name: 'Generate Attendances',
        });
    }

    async onBulkApproveAttendances() {
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'orbit.attendance.approve.wizard',
            views: [[false, 'form']],
            target: 'new',
            name: 'Bulk Approve Attendances',
        });
    }

    async onBulkAbsentAttendances() {
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'orbit.attendance.absent.wizard',
            views: [[false, 'form']],
            target: 'new',
            name: 'Bulk Absent Attendances',
        });
    }
}

registry.category("views").add("attendance_generator_list", {
    ...listView,
    Controller: AttendanceListController,
    buttonTemplate: "orbit_hr_workspace.ListView.Buttons",
});

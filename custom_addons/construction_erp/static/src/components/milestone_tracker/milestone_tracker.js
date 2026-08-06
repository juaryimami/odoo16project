/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { MilestoneConfigCard } from "./milestone_config_card";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
const { Component, useState, onWillUpdateProps } = owl;

export class MilestoneTracker extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.state = useState({
            milestones: this._parseMilestones(this.props.value)
        });

        onWillUpdateProps((nextProps) => {
            this.state.milestones = this._parseMilestones(nextProps.value);
        });
    }

    _parseMilestones(value) {
        try {
            return JSON.parse(value || "[]");
        } catch (e) {
            return [];
        }
    }

    async refresh() {
        // Force a specific field load to update the record in cache
        await this.props.record.load();
        // Manually push the new data into the reactive state to bypass any Odoo framework delays
        this.state.milestones = this._parseMilestones(this.props.record.data.milestone_progress_data);
    }

    async addWorkMilestone() {
        const jobId = this.props.record.resId;
        if (!jobId) return;

        // Calculate next sequence to ensure it's at the end
        const sequences = this.state.milestones.map(m => m.sequence || 0);
        const nextSequence = (sequences.length > 0 ? Math.max(...sequences) : 0) + 10;

        this.dialog.add(MilestoneConfigCard, {
            jobOrderId: jobId,
            mode: 'create',
            nextSequence: nextSequence,
            onSave: async () => {
                await this.refresh();
                this.notification.add("New work section added.", { type: "info" });
            }
        });
    }

    async deleteMilestone(milestoneId) {
        this.dialog.add(ConfirmationDialog, {
            body: "Are you sure you want to delete this work section? This will re-order the remaining roadmap.",
            confirm: async () => {
                await this.orm.unlink("construction.job.milestone", [milestoneId]);
                await this.refresh();
                this.notification.add("Section removed.", { type: "warning" });
            },
            cancel: () => {},
        });
    }

    async openMilestone(milestoneId) {
        this.dialog.add(MilestoneConfigCard, {
            milestoneId: milestoneId,
            mode: 'edit',
            onSave: async () => {
                await this.refresh();
            }
        });
    }

    getStatusClass(state) {
        const mapping = {
            'pending': 'milestone-locked',
            'in_progress': 'milestone-active',
            'inspection': 'milestone-review',
            'approved': 'milestone-done',
            'billed': 'milestone-done'
        };
        return mapping[state] || 'milestone-locked';
    }
}

MilestoneTracker.template = "construction_erp.MilestoneTracker";
MilestoneTracker.supportedFieldTypes = ["text"];

registry.category("fields").add("milestone_tracker", MilestoneTracker);

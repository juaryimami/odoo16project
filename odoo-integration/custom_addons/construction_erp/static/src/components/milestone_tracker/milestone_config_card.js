/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
const { Component, useState, onWillStart } = owl;

export class MilestoneConfigCard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            name: this.props.mode === 'create' ? "New Work Section" : "",
            description: "",
            percentage: 0,
            availableChecklists: [],
            selectedChecklistIds: new Set(),
            isReadonly: false,
        });

        onWillStart(async () => {
            let jobId = this.props.jobOrderId;

            if (this.props.mode === 'edit') {
                const data = await this.orm.read("construction.job.milestone", [this.props.milestoneId], 
                    ["name", "description", "percentage", "job_order_id", "checklist_ids", "state"]);
                
                if (data.length) {
                    const milestone = data[0];
                    this.state.name = milestone.name;
                    this.state.description = milestone.description ? milestone.description.replace(/<[^>]*>/g, '') : "";
                    this.state.percentage = milestone.percentage;
                    this.state.selectedChecklistIds = new Set(milestone.checklist_ids);
                    this.state.isReadonly = ['approved', 'billed'].includes(milestone.state);
                    jobId = Array.isArray(milestone.job_order_id) ? milestone.job_order_id[0] : milestone.job_order_id;
                }
            }
            
            // Always load Job Checklists for pinning
            if (jobId) {
                const checklists = await this.orm.searchRead("construction.job.checklist.line", 
                    [ ["job_order_id", "=", jobId] ], 
                    ["name", "is_done", "mandatory"]
                );
                this.state.availableChecklists = checklists;
            }
        });
    }

    toggleChecklist(checklistId) {
        if (this.state.selectedChecklistIds.has(checklistId)) {
            this.state.selectedChecklistIds.delete(checklistId);
        } else {
            this.state.selectedChecklistIds.add(checklistId);
        }
    }

    async save() {
        try {
            const vals = {
                name: this.state.name,
                description: this.state.description,
                percentage: this.state.percentage,
                checklist_ids: [[6, 0, Array.from(this.state.selectedChecklistIds)]]
            };

            if (this.props.mode === 'create') {
                vals.job_order_id = this.props.jobOrderId;
                vals.milestone_type = 'work';
                vals.sequence = this.props.nextSequence || 0;
                await this.orm.create("construction.job.milestone", [vals]);
            } else {
                await this.orm.write("construction.job.milestone", [this.props.milestoneId], vals);
            }

            this.notification.add(this.props.mode === 'create' ? "Section added successfully." : "Changes saved.", { type: "success" });
            this.props.close();
            if (this.props.onSave) await this.props.onSave();
        } catch (e) {
            this.notification.add("Failed to save changes.", { type: "danger" });
        }
    }
}

MilestoneConfigCard.template = "construction_erp.MilestoneConfigCard";
MilestoneConfigCard.components = { Dialog };

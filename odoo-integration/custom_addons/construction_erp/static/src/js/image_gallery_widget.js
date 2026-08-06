/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component, onWillStart } = owl;

export class ConstructionImageGalleryWidget extends Component {
    setup() {
        this.action = useService("action");
    }

    get images() {
        // Parse Native Form fields passed securely into the Custom UI Domain
        if (!this.props.value || !this.props.value.records) {
            return [];
        }
        return this.props.value.records.map((rec) => {
            return {
                id: rec.data.id,
                name: rec.data.name || "Site Progress",
                date: rec.data.date ? rec.data.date.toFormat("yyyy-MM-dd") : ""
            };
        });
    }

    openImage(id) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'construction.project.image',
            res_id: id,
            views: [[false, 'form']],
            target: 'new',
        });
    }
}

ConstructionImageGalleryWidget.template = "construction_erp.ImageGalleryWidgetTemplate";
ConstructionImageGalleryWidget.props = {
    ...standardFieldProps,
};

// Register natively as a core accessible Widget inside entire ERP loop safely
registry.category("fields").add("construction_image_gallery", ConstructionImageGalleryWidget);

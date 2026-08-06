/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CustomerPortalDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            properties: [],
            loading: true,
        });

        onWillStart(async () => {
            await this.loadProperties();
        });
    }

    async loadProperties() {
        try {
            const res = await this.rpc("/api/customer/properties", {});
            this.state.properties = res.properties;
        } catch (e) {
            console.error("Failed to load properties", e);
        } finally {
            this.state.loading = false;
        }
    }

    viewProperty(propertyId) {
        this.props.navigateTo("property_details", { propertyId });
    }
}

CustomerPortalDashboard.template = "construction_erp.CustomerPortalDashboard";
CustomerPortalDashboard.props = {
    navigateTo: Function,
};

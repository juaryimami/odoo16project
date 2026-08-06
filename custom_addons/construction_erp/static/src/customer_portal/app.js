/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { CustomerPortalLogin } from "./login";
import { CustomerPortalDashboard } from "./dashboard";
import { CustomerPortalPropertyDetails } from "./property_details";

import { CustomerPortalProfile } from "./profile";

export class CustomerPortalApp extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            loading: true,
            loggedIn: false,
            userName: "",
            partnerId: null,
            currentRoute: "dashboard",
            currentPropertyId: null,
        });

        onWillStart(async () => {
            await this.checkSession();
        });
    }

    async checkSession() {
        try {
            const res = await this.rpc("/api/customer/session", {});
            if (res.logged_in) {
                this.state.loggedIn = true;
                this.state.userName = res.name;
                this.state.partnerId = res.partner_id;
            } else {
                this.state.loggedIn = false;
            }
        } catch (e) {
            this.state.loggedIn = false;
        } finally {
            this.state.loading = false;
        }
    }

    onLogin(userData) {
        this.state.loggedIn = true;
        this.state.userName = userData.name;
        this.state.partnerId = userData.partner_id;
        this.state.currentRoute = "dashboard";
    }

    async onLogout() {
        this.state.loading = true;
        try {
            await this.rpc("/web/session/destroy", {});
        } catch (e) {}
        this.state.loggedIn = false;
        this.state.userName = "";
        this.state.partnerId = null;
        this.state.currentRoute = "dashboard";
        this.state.loading = false;
    }

    navigateHome() {
        this.navigateTo("dashboard");
    }

    navigateTo(route, params = {}) {
        this.state.currentRoute = route;
        if (route === "property_details") {
            this.state.currentPropertyId = params.propertyId;
        }
    }
}

CustomerPortalApp.template = "construction_erp.CustomerPortalApp";
CustomerPortalApp.components = {
    CustomerPortalLogin,
    CustomerPortalDashboard,
    CustomerPortalPropertyDetails,
    CustomerPortalProfile,
};

/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CustomerPortalLogin extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            username: "",
            password: "",
            loading: false,
            error: null,
        });
    }

    async submitLogin() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const res = await this.rpc("/api/customer/login", {
                login: this.state.username,
                password: this.state.password,
            });
            if (res.success) {
                this.props.onLogin(res);
            } else {
                this.state.error = res.error || "Login failed";
            }
        } catch (e) {
            this.state.error = "Connection error. Please try again.";
        } finally {
            this.state.loading = false;
        }
    }
}

CustomerPortalLogin.template = "construction_erp.CustomerPortalLogin";
CustomerPortalLogin.props = {
    onLogin: Function,
};

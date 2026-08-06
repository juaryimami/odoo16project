/** @odoo-module **/

import { mount, whenReady } from "@odoo/owl";
import { CustomerPortalApp } from "./app";
import { templates } from "@web/core/assets";
import { makeEnv, startServices } from "@web/env";

whenReady(async () => {
    const root = document.getElementById('customer_portal_app');
    if (root) {
        const env = await makeEnv();
        await startServices(env);
        mount(CustomerPortalApp, root, { templates, env, dev: true });
    }
});

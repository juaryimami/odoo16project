/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CustomerPortalProfile extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            oldPassword: "",
            newPassword: "",
            confirmPassword: "",
            showNewPassword: false,
            showConfirmPassword: false,
            loading: false,
            error: null,
            success: false,
            avatarTimestamp: new Date().getTime(),
            uploadingAvatar: false,
        });
    }

    async onAvatarChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;

        this.state.uploadingAvatar = true;
        this.state.error = null;

        const reader = new FileReader();
        reader.onload = async (e) => {
            const dataUrl = e.target.result;
            const base64Data = dataUrl.split(',')[1];
            try {
                const res = await this.rpc("/api/customer/update_avatar", {
                    image_base64: base64Data
                });
                if (res.success) {
                    this.state.avatarTimestamp = new Date().getTime();
                    window.location.reload();
                } else {
                    this.state.error = res.error || "Failed to update profile picture.";
                }
            } catch (error) {
                this.state.error = "Connection error. Please try again.";
            } finally {
                this.state.uploadingAvatar = false;
            }
        };
        reader.readAsDataURL(file);
    }

    toggleNewPassword() {
        this.state.showNewPassword = !this.state.showNewPassword;
    }

    toggleConfirmPassword() {
        this.state.showConfirmPassword = !this.state.showConfirmPassword;
    }

    async submitPasswordChange() {
        this.state.error = null;
        this.state.success = false;

        if (this.state.newPassword !== this.state.confirmPassword) {
            this.state.error = "New passwords do not match.";
            return;
        }

        if (this.state.newPassword.length < 4) {
            this.state.error = "Password must be at least 4 characters long.";
            return;
        }

        this.state.loading = true;
        try {
            const res = await this.rpc("/api/customer/change_password", {
                old_password: this.state.oldPassword,
                new_password: this.state.newPassword,
            });
            if (res.success) {
                this.state.success = true;
                this.state.oldPassword = "";
                this.state.newPassword = "";
                this.state.confirmPassword = "";
            } else {
                this.state.error = res.error || "Failed to change password.";
            }
        } catch (e) {
            this.state.error = "Connection error. Please try again.";
        } finally {
            this.state.loading = false;
        }
    }
}

CustomerPortalProfile.template = "construction_erp.CustomerPortalProfile";
CustomerPortalProfile.props = {
    navigateTo: Function,
    partnerId: { type: Number, optional: true },
};

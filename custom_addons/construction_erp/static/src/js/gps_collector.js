/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component, useState } = owl;

export class GpsCollectorWidget extends Component {
    setup() {
        this.notification = useService("notification");
        this.state = useState({
            loading: false,
            error: null,
        });
    }

    async collectGps() {
        if (!navigator.geolocation) {
            this.state.error = "Geolocation is not supported by this browser.";
            return;
        }

        this.state.loading = true;
        this.state.error = null;

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                try {
                    // Update the model fields directly on the record
                    await this.props.record.update({
                        site_latitude: lat,
                        site_longitude: lng,
                    });
                    
                    this.notification.add("Location captured successfully!", {
                        type: "success",
                        title: "GPS Success",
                    });
                } catch (err) {
                    this.state.error = "Failed to update record fields.";
                } finally {
                    this.state.loading = false;
                }
            },
            (error) => {
                this.state.loading = false;
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        this.state.error = "User denied the request for Geolocation.";
                        break;
                    case error.POSITION_UNAVAILABLE:
                        this.state.error = "Location information is unavailable.";
                        break;
                    case error.TIMEOUT:
                        this.state.error = "The request to get user location timed out.";
                        break;
                    default:
                        this.state.error = "An unknown error occurred.";
                        break;
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }
}

GpsCollectorWidget.template = "construction_erp.GpsCollectorButton";
GpsCollectorWidget.props = {
    ...standardFieldProps,
};

// Register as a field widget (can be applied to any dummy field)
registry.category("fields").add("gps_collector", GpsCollectorWidget);

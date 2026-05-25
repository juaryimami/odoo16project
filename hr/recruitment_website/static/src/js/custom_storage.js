/** @odoo-module **/

import { Component, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class RecruitmentStorage extends Component {
    setup() {
        this.state = useState({
            profiles: this.getProfiles(),
        });

        this.rpc = useService("rpc");

        // Load profiles on mount
        onMounted(() => {
            this.displayProfiles();
        });
    }

    getProfiles() {
        const profiles = localStorage.getItem("candidateProfiles");
        return profiles ? JSON.parse(profiles) : [];
    }

    storeProfiles(profiles) {
        localStorage.setItem("candidateProfiles", JSON.stringify(profiles));
    }

    addProfile(profile) {
        const profiles = this.getProfiles();
        profiles.push(profile);
        this.storeProfiles(profiles);
        this.state.profiles = profiles; // Update state
    }

    displayProfiles() {
        const profileContainer = document.getElementById("profileContainer");
        if (profileContainer) {
            profileContainer.innerHTML = "";
            this.state.profiles.forEach((profile, index) => {
                const profileHtml = `
                    <div class="profile">
                        <h4>Education ${index + 1}</h4>
                        <p><strong>Institution:</strong> ${profile.institution}</p>
                        <p><strong>Degree:</strong> ${profile.degree}</p>
                        <p><strong>Field of Study:</strong> ${profile.fieldOfStudy}</p>
                        <p><strong>Start Date:</strong> ${profile.startDate}</p>
                        <p><strong>End Date:</strong> ${profile.endDate}</p>
                    </div>
                `;
                profileContainer.insertAdjacentHTML("beforeend", profileHtml);
            });
        }
    }

    handleSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const profile = {
            institution: form.institution.value,
            degree: form.degree.value,
            fieldOfStudy: form.fieldOfStudy.value,
            startDate: form.startDate.value,
            endDate: form.endDate.value,
        };
        this.addProfile(profile);
        this.displayProfiles();
        form.reset();
    }
}

// Mount the component manually (if used outside an existing Odoo component)
document.addEventListener("DOMContentLoaded", () => {
    const recruitmentStorage = new RecruitmentStorage();
    document.getElementById("educationForm").addEventListener("submit", (e) => recruitmentStorage.handleSubmit(e));
});
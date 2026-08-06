/** @odoo-module **/

import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class PolicyDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            data: null,
        });
        this.chartCanvas = useRef("chartCanvas");

        onWillStart(async () => {
            // Load Chart.js if not already loaded by Odoo
            await loadJS("/web/static/lib/Chart/Chart.js");
            // Fetch dashboard data
            this.state.data = await this.rpc("/web/dataset/call_kw/hr.policy.attestation/get_dashboard_data", {
                model: "hr.policy.attestation",
                method: "get_dashboard_data",
                args: [[]],
                kwargs: {},
            });
        });

        onMounted(() => {
            if (this.state.data && this.chartCanvas.el) {
                this.renderChart();
            }
        });
    }

    renderChart() {
        const ctx = this.chartCanvas.el.getContext('2d');
        const chartData = this.state.data.chart;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Agreed',
                        data: chartData.agreed,
                        backgroundColor: '#71639e',
                        borderWidth: 0
                    },
                    {
                        label: 'Pending Action',
                        data: chartData.pending,
                        backgroundColor: '#e9ecef',
                        borderWidth: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    xAxes: [{
                        stacked: true,
                        gridLines: { display: false }
                    }],
                    yAxes: [{
                        stacked: true,
                        ticks: { beginAtZero: true, stepSize: 1 }
                    }]
                },
                legend: {
                    position: 'bottom'
                }
            }
        });
    }
}

PolicyDashboard.template = "hr_policy_attestation.PolicyDashboard";

registry.category("actions").add("hr_policy_dashboard_owl", PolicyDashboard);

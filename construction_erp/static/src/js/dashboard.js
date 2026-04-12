/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, onMounted, useState } = owl;

export class ConstructionDashboardMain extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            metrics: {},
            loading: true,
            active_album: null
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadMetrics();
        });

        onMounted(() => {
            this.renderCharts();
        });

        owl.onPatched(() => {
            this.renderCharts();
        });
    }

    async loadMetrics() {
        this.state.is_loading = true;
        this.state.metrics = await this.orm.call("construction.dashboard.backend", "get_construction_statistics", []);
        this.state.is_loading = false;
    }

    renderCharts() {
        if(this.state.is_loading) return;

        // 1. Category Burn Velocity Chart (Grouped Bar)
        const burnCtx = document.getElementById("categoryBurnChart");
        if(burnCtx && window.Chart) {
            new Chart(burnCtx, {
                type: 'bar',
                data: {
                    labels: ['Material', 'Labor', 'Equipment', 'Vehicle', 'Overhead'],
                    datasets: [
                        {
                            label: 'Planned Budget',
                            data: this.state.metrics.charts.burn_data.budget,
                            backgroundColor: 'rgba(78, 115, 223, 0.8)',
                            borderColor: '#4e73df',
                            borderWidth: 1
                        },
                        {
                            label: 'Actual Spent',
                            data: this.state.metrics.charts.burn_data.actual,
                            backgroundColor: 'rgba(28, 200, 138, 0.8)',
                            borderColor: '#1cc88a',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { drawBorder: false, color: '#f2f2f2' }
                        },
                        x: {
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: { backgroundColor: '#2e3d55', padding: 12 }
                    }
                }
            });
        }

        // 2. Contractor Site Pulse (Donut)
        const pulseCtx = document.getElementById("contractorPulseChart");
        if(pulseCtx && window.Chart) {
            new Chart(pulseCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Offered', 'Active', 'Inspection', 'Rework'],
                    datasets: [{
                        data: [
                            this.state.metrics.charts.contractor_pulse.offered,
                            this.state.metrics.charts.contractor_pulse.active,
                            this.state.metrics.charts.contractor_pulse.inspection,
                            this.state.metrics.charts.contractor_pulse.rework,
                        ],
                        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e'],
                        hoverOffset: 10,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '75%',
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12, padding: 15 } }
                    }
                }
            });
        }

        // 3. Yearly Sales Pulse (Area Line Chart) - Multi-Project Support
        const salesCtx = document.getElementById("yearlySalesChart");
        if(salesCtx && window.Chart) {
            const rawDatasets = this.state.metrics.charts.sales_analysis.datasets || [];
            const palette = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#5a5c69', '#6610f2', '#e83e8c'];
            
            const datasets = rawDatasets.map((ds, index) => {
                const color = palette[index % palette.length];
                return {
                    label: ds.label,
                    data: ds.data,
                    fill: true,
                    backgroundColor: color + '1A', // 10% opacity for area fill
                    borderColor: color,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: color,
                    pointBorderWidth: 2
                };
            });

            new Chart(salesCtx, {
                type: 'line',
                data: {
                    labels: this.state.metrics.charts.sales_analysis.labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true, position: 'top', align: 'end' },
                        tooltip: { mode: 'index', intersect: false }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true, 
                            grid: { borderDash: [2, 2], color: '#f2f2f2' },
                            ticks: { callback: (value) => value.toLocaleString() }
                        },
                        x: { grid: { display: false } }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: { backgroundColor: '#2e3d55', padding: 12 }
                    }
                }
            });
        }

        // 4. Portfolio Lifecycle Analysis (Horizontal Bar Chart)
        const phaseCtx = document.getElementById("projectPhaseChart");
        if(phaseCtx && window.Chart) {
            new Chart(phaseCtx, {
                type: 'bar',
                data: {
                    labels: this.state.metrics.charts.phase_labels,
                    datasets: [{
                        label: 'Project Count',
                        data: this.state.metrics.charts.phase_data,
                        backgroundColor: 'rgba(54, 185, 204, 0.2)',
                        borderColor: '#36b9cc',
                        borderWidth: 2,
                        borderRadius: 5,
                        barThickness: 20
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { backgroundColor: '#2e3d55', padding: 10 }
                    },
                    scales: {
                        x: { 
                            beginAtZero: true, 
                            ticks: { stepSize: 1, precision: 0 },
                            grid: { color: '#f2f2f2' }
                        },
                        y: { 
                            grid: { display: false }
                        }
                    }
                }
            });
        }
    }

    // Strategic Navigation
    openProjects() { this.action.doAction('construction_erp.action_construction_projects'); }
    openCompliance() { this.action.doAction('construction_erp.action_construction_compliance'); }
    openMaterials() { this.action.doAction('construction_erp.action_construction_materials'); }
    openEstimates() { this.action.doAction('construction_erp.action_construction_estimate'); }
    openInspections() { this.action.doAction('construction_erp.action_construction_inspection'); }
    openRequisitions() { this.action.doAction('construction_erp.action_material_requisition'); }
    openContractors() { this.action.doAction('base.action_partner_supplier_form', {domain: [['is_contractor', '=', true]]}); }
    openPurchase() { this.action.doAction('purchase.purchase_form_action', {domain: [['project_id.project_type', '=', 'construction']]}); }
    
    openGallery(album) {
        this.state.active_album = album;
    }
    closeGallery() {
        this.state.active_album = null;
    }
    
    openTasks() { this.action.doAction('project.action_view_task', {domain: [['project_id.project_type', '=', 'construction']]}); }
}

ConstructionDashboardMain.template = "construction_erp.OwlDashboardNative";
registry.category("actions").add("construction_dashboard_client_action", ConstructionDashboardMain);

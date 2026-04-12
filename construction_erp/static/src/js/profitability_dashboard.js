/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, onMounted, useState } = owl;

export class ProjectProfitabilityMain extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            metrics: [],
            totals: {
                budget: 0,
                actual: 0,
                certified: 0,
                paid: 0,
                retention: 0
            },
            is_loading: true
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    async loadData() {
        this.state.is_loading = true;
        const result = await this.orm.call("construction.dashboard.backend", "get_profitability_metrics", []);
        this.state.metrics = result;
        
        // Calculate Portfolio Totals
        this.state.totals = result.reduce((acc, curr) => {
            acc.budget += curr.budget;
            acc.actual += curr.actual;
            acc.certified += curr.certified;
            acc.paid += curr.paid;
            acc.retention += curr.retention;
            return acc;
        }, { budget: 0, actual: 0, certified: 0, paid: 0, retention: 0 });

        this.state.is_loading = false;
        if (this.budgetActualChart) this.renderCharts(); // Re-render if refresh
    }

    renderCharts() {
        if(this.state.is_loading) return;

        // 1. Budget vs Actual Bar Chart
        const bvaCtx = document.getElementById("budgetActualChart");
        if(bvaCtx && window.Chart) {
            if (this.budgetActualChart) this.budgetActualChart.destroy();
            this.budgetActualChart = new Chart(bvaCtx, {
                type: 'bar',
                data: {
                    labels: this.state.metrics.map(m => m.project_name),
                    datasets: [
                        { label: 'Budgeted Cost', data: this.state.metrics.map(m => m.budget), backgroundColor: '#7367f0' },
                        { label: 'Actual Spend', data: this.state.metrics.map(m => m.actual), backgroundColor: '#ea5455' }
                    ]
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true } }
                }
            });
        }

        // 2. Category Breakdown Pie Chart (Cumulative)
        const catCtx = document.getElementById("categoryBreakdownChart");
        if(catCtx && window.Chart) {
            const catTotals = this.state.metrics.reduce((acc, curr) => {
                acc.material += curr.categories.material;
                acc.labor += curr.categories.labor;
                acc.overhead += curr.categories.overhead;
                acc.fleet += curr.categories.fleet;
                acc.equipment += curr.categories.equipment;
                return acc;
            }, { material: 0, labor: 0, overhead: 0, fleet: 0, equipment: 0 });

            if (this.categoryChart) this.categoryChart.destroy();
            this.categoryChart = new Chart(catCtx, {
                type: 'polarArea',
                data: {
                    labels: ['Materials', 'Labor', 'Overhead', 'Fleet', 'Equipment'],
                    datasets: [{
                        data: [catTotals.material, catTotals.labor, catTotals.overhead, catTotals.fleet, catTotals.equipment],
                        backgroundColor: [
                            'rgba(115, 103, 240, 0.7)',
                            'rgba(40, 199, 111, 0.7)',
                            'rgba(255, 159, 67, 0.7)',
                            'rgba(234, 84, 85, 0.7)',
                            'rgba(0, 207, 232, 0.7)'
                        ]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        }
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
    }

    openProject(id) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            res_id: id,
            view_mode: 'form',
            target: 'current'
        });
    }
}

ProjectProfitabilityMain.template = "construction_erp.ProjectProfitabilityTemplate";
registry.category("actions").add("project_profitability_dashboard_action", ProjectProfitabilityMain);

/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CustomerPortalPropertyDetails extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            loading: true,
            property: null,
            activeTab: "installments",
            
            // Installments Pagination
            installments: [],
            installmentsTotal: 0,
            installmentsOffset: 0,
            installmentsLimit: 15,
            loadingInstallments: false,
            
            // Invoices Pagination
            invoices: [],
            invoicesTotal: 0,
            invoicesOffset: 0,
            invoicesLimit: 15,
            loadingInvoices: false,
            
            // Documents Pagination
            documents: [],
            documentsTotal: 0,
            documentsOffset: 0,
            documentsLimit: 15,
            loadingDocuments: false,
        });

        onWillStart(async () => {
            await this.loadPropertyDetails();
            await this.loadInstallments();
        });
    }

    async loadPropertyDetails() {
        try {
            const res = await this.rpc("/api/customer/property_details", {
                order_id: this.props.propertyId
            });
            if (res.error) {
                this.props.navigateTo("dashboard");
            } else {
                this.state.property = res;
            }
        } catch (e) {
            console.error("Failed to load details", e);
        } finally {
            this.state.loading = false;
        }
    }

    // Tabs
    async setTab(tab) {
        this.state.activeTab = tab;
        if (tab === 'installments' && this.state.installments.length === 0) {
            await this.loadInstallments();
        } else if (tab === 'invoices' && this.state.invoices.length === 0) {
            await this.loadInvoices();
        } else if (tab === 'documents' && this.state.documents.length === 0) {
            await this.loadDocuments();
        }
    }

    // Installments
    async loadInstallments() {
        this.state.loadingInstallments = true;
        try {
            const res = await this.rpc("/api/customer/installments", {
                order_id: this.props.propertyId,
                limit: this.state.installmentsLimit,
                offset: this.state.installmentsOffset
            });
            this.state.installments = res.lines;
            this.state.installmentsTotal = res.total;
        } finally {
            this.state.loadingInstallments = false;
        }
    }
    
    async prevInstallments() {
        if (this.state.installmentsOffset >= this.state.installmentsLimit) {
            this.state.installmentsOffset -= this.state.installmentsLimit;
            await this.loadInstallments();
        }
    }
    
    async nextInstallments() {
        if (this.state.installmentsOffset + this.state.installmentsLimit < this.state.installmentsTotal) {
            this.state.installmentsOffset += this.state.installmentsLimit;
            await this.loadInstallments();
        }
    }

    // Invoices
    async loadInvoices() {
        this.state.loadingInvoices = true;
        try {
            const res = await this.rpc("/api/customer/invoices", {
                order_id: this.props.propertyId,
                limit: this.state.invoicesLimit,
                offset: this.state.invoicesOffset
            });
            this.state.invoices = res.invoices;
            this.state.invoicesTotal = res.total;
        } finally {
            this.state.loadingInvoices = false;
        }
    }
    
    async prevInvoices() {
        if (this.state.invoicesOffset >= this.state.invoicesLimit) {
            this.state.invoicesOffset -= this.state.invoicesLimit;
            await this.loadInvoices();
        }
    }
    
    async nextInvoices() {
        if (this.state.invoicesOffset + this.state.invoicesLimit < this.state.invoicesTotal) {
            this.state.invoicesOffset += this.state.invoicesLimit;
            await this.loadInvoices();
        }
    }

    // Documents
    async loadDocuments() {
        this.state.loadingDocuments = true;
        try {
            const res = await this.rpc("/api/customer/documents", {
                order_id: this.props.propertyId,
                limit: this.state.documentsLimit,
                offset: this.state.documentsOffset
            });
            this.state.documents = res.documents;
            this.state.documentsTotal = res.total;
        } finally {
            this.state.loadingDocuments = false;
        }
    }
    
    async prevDocuments() {
        if (this.state.documentsOffset >= this.state.documentsLimit) {
            this.state.documentsOffset -= this.state.documentsLimit;
            await this.loadDocuments();
        }
    }
    
    async nextDocuments() {
        if (this.state.documentsOffset + this.state.documentsLimit < this.state.documentsTotal) {
            this.state.documentsOffset += this.state.documentsLimit;
            await this.loadDocuments();
        }
    }
}

CustomerPortalPropertyDetails.template = "construction_erp.CustomerPortalPropertyDetails";
CustomerPortalPropertyDetails.props = {
    propertyId: Number,
    navigateTo: Function,
};

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class ProjectReportWizard(models.TransientModel):
    _name = 'project.report.wizard'
    _description = 'Comprehensive Project Analytical Wizard'

    project_id = fields.Many2one('project.project', string='Select Project', required=True)
    report_type = fields.Selection([
        ('pdf', 'Standard QWeb PDF'),
        ('excel', 'Deep Analytic Excel (.xlsx)')
    ], string='Report Format', default='excel', required=True)
    
    excel_file = fields.Binary('Excel Payload', readonly=True)
    file_name = fields.Char('File Name', readonly=True)
    state = fields.Selection([
        ('choose', 'Configuration'),
        ('get', 'Download Available')
    ], default='choose')

    def action_generate_report(self):
        self.ensure_one()
        if self.report_type == 'pdf':
            return self.env.ref('construction_erp.action_report_project_comprehensive').report_action(self.project_id)
        elif self.report_type == 'excel':
            if not xlsxwriter:
                raise UserError(_("The Python library 'xlsxwriter' is required to generate Native Excel matrices."))
            return self._generate_excel_export()

    def _generate_excel_export(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        header_format = workbook.add_format({'bold': True, 'bg_color': '#E0E0E0', 'border': 1, 'font_size': 12})
        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#005b96', 'font_color': 'white'})
        currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        standard_format = workbook.add_format({'border': 1})
        
        # =========================================================
        # SHEET 1: Master Financials
        # =========================================================
        sheet1 = workbook.add_worksheet('Executive Financials')
        sheet1.set_column('A:B', 30)
        
        sheet1.merge_range('A1:B1', f"Master Diagnostics: {self.project_id.name}", title_format)
        
        sheet1.write('A3', 'Total Analytical Expenses', header_format)
        sheet1.write('B3', self.project_id.total_expense, currency_format)
        
        sheet1.write('A4', 'Total Validated Income', header_format)
        sheet1.write('B4', self.project_id.total_collected, currency_format)
        
        sheet1.write('A5', 'Net Systemic Profitability', header_format)
        sheet1.write('B5', self.project_id.profitability, currency_format)

        sheet1.write('A7', 'Physical Wastage Events Logged', header_format)
        sheet1.write('B7', self.project_id.scrap_count, standard_format)
        
        # =========================================================
        # SHEET 2: Phase Estimates Breakdown
        # =========================================================
        sheet2 = workbook.add_worksheet('Phase Budgets')
        sheet2.set_column('A:C', 25)
        sheet2.merge_range('A1:C1', 'Approved Master Plan Estimates', title_format)
        
        sheet2.write('A3', 'Target Phase', header_format)
        sheet2.write('B3', 'Core Material Product', header_format)
        sheet2.write('C3', 'Approved Cost Allocation', header_format)
        
        row = 3
        for line in self.project_id.estimate_line_ids:
            phase_name = line.estimate_id.phase_id.name if line.estimate_id.phase_id else 'General'
            product_name = line.product_id.name if line.product_id else 'N/A'
            sheet2.write(row, 0, phase_name, standard_format)
            sheet2.write(row, 1, product_name, standard_format)
            sheet2.write(row, 2, line.total_cost, currency_format)
            row += 1

        # =========================================================
        # SHEET 3: Material Requisitions
        # =========================================================
        requisitions = self.env['construction.material.requisition'].search([('project_id', '=', self.project_id.id)])
        sheet3 = workbook.add_worksheet('Material Requisitions')
        sheet3.set_column('A:E', 20)
        sheet3.write('A1', 'Requisition Ref', header_format)
        sheet3.write('B1', 'Request Date', header_format)
        sheet3.write('C1', 'Requested By', header_format)
        sheet3.write('D1', 'Status', header_format)
        sheet3.write('E1', 'Items Count', header_format)
        
        row = 1
        for req in requisitions:
            sheet3.write(row, 0, req.name, standard_format)
            sheet3.write(row, 1, str(req.request_date), standard_format)
            sheet3.write(row, 2, req.requested_by.name if req.requested_by else '', standard_format)
            sheet3.write(row, 3, req.state, standard_format)
            sheet3.write(row, 4, len(req.line_ids), standard_format)
            row += 1

        # =========================================================
        # SHEET 4: Stock Transfers (Movements)
        # =========================================================
        sheet4 = workbook.add_worksheet('Stock Transfers')
        sheet4.set_column('A:E', 25)
        sheet4.write('A1', 'Reference', header_format)
        sheet4.write('B1', 'Source Document', header_format)
        sheet4.write('C1', 'Source Location', header_format)
        sheet4.write('D1', 'Destination', header_format)
        sheet4.write('E1', 'Status', header_format)
        
        row = 1
        pickings = requisitions.mapped('picking_ids')
        for pick in pickings:
            sheet4.write(row, 0, pick.name, standard_format)
            sheet4.write(row, 1, pick.origin or '', standard_format)
            sheet4.write(row, 2, pick.location_id.name, standard_format)
            sheet4.write(row, 3, pick.location_dest_id.name, standard_format)
            sheet4.write(row, 4, pick.state, standard_format)
            row += 1

        # =========================================================
        # SHEET 5: Analytic Expenses
        # =========================================================
        sheet5 = workbook.add_worksheet('Analytic Expenses')
        sheet5.set_column('A:D', 25)
        sheet5.write('A1', 'Date', header_format)
        sheet5.write('B1', 'Description', header_format)
        sheet5.write('C1', 'Partner / Vendor', header_format)
        sheet5.write('D1', 'Amount', header_format)
        
        row = 1
        analytic_lines = self.env['account.analytic.line'].search([('account_id', '=', self.project_id.analytic_account_id.id)])
        for aline in analytic_lines:
            sheet5.write(row, 0, str(aline.date), standard_format)
            sheet5.write(row, 1, aline.name, standard_format)
            sheet5.write(row, 2, aline.partner_id.name if aline.partner_id else '', standard_format)
            sheet5.write(row, 3, aline.amount, currency_format)
            row += 1

        # =========================================================
        # SHEET 6: Purchase Orders (Procurement)
        # =========================================================
        sheet6 = workbook.add_worksheet('Procurement (POs)')
        sheet6.set_column('A:E', 25)
        sheet6.write('A1', 'PO Reference', header_format)
        sheet6.write('B1', 'Vendor', header_format)
        sheet6.write('C1', 'Source Requisition', header_format)
        sheet6.write('D1', 'Amount Total', header_format)
        sheet6.write('E1', 'Status', header_format)
        
        row = 1
        pos = requisitions.mapped('purchase_ids')
        for po in pos:
            sheet6.write(row, 0, po.name, standard_format)
            sheet6.write(row, 1, po.partner_id.name if po.partner_id else '', standard_format)
            sheet6.write(row, 2, po.origin or '', standard_format)
            sheet6.write(row, 3, po.amount_total, currency_format)
            sheet6.write(row, 4, po.state, standard_format)
            row += 1

        # =========================================================
        # SHEET 7: Real Estate Commercial Sales
        # =========================================================
        sheet7 = workbook.add_worksheet('Real Estate Sales')
        sheet7.set_column('A:G', 20)
        sheet7.write('A1', 'Unit ID', header_format)
        sheet7.write('B1', 'Type', header_format)
        sheet7.write('C1', 'Client', header_format)
        sheet7.write('D1', 'Status', header_format)
        sheet7.write('E1', 'Sale Price', header_format)
        sheet7.write('F1', 'Amount Paid', header_format)
        sheet7.write('G1', 'Remaining Balance', header_format)
        
        row = 1
        units = self.env['real_estate.unit'].search([('project_id', '=', self.project_id.id), ('status', 'in', ['reserved', 'sold'])])
        for unit in units:
            sheet7.write(row, 0, unit.name, standard_format)
            sheet7.write(row, 1, unit.unit_type.capitalize() if unit.unit_type else '', standard_format)
            sheet7.write(row, 2, unit.client_id.name if unit.client_id else '', standard_format)
            sheet7.write(row, 3, unit.status.capitalize(), standard_format)
            sheet7.write(row, 4, unit.price, currency_format)
            sheet7.write(row, 5, unit.amount_paid, currency_format)
            sheet7.write(row, 6, unit.amount_remaining, currency_format)
            row += 1

        workbook.close()
        output.seek(0)
        
        # Encode payload natively replacing state variable
        excel_payload = base64.b64encode(output.read())
        self.write({
            'excel_file': excel_payload,
            'file_name': f"Executive_Analytics_{self.project_id.name.replace(' ', '_')}.xlsx",
            'state': 'get'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

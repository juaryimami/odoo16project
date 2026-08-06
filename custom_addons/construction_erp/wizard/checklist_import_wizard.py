# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import csv
import io

try:
    import xlrd
except ImportError:
    xlrd = None

class ConstructionChecklistImportWizard(models.TransientModel):
    _name = 'construction.checklist.import.wizard'
    _description = 'Import Checklist Items from Excel/CSV'

    template_id = fields.Many2one('construction.checklist.template', string='Checklist Template', required=True)
    file = fields.Binary(string='File Content')
    file_name = fields.Char(string='File Name')

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("Please upload a file before importing."))

        file_content = base64.b64decode(self.file)
        lines_data = []

        if self.file_name and self.file_name.lower().endswith('.csv'):
            lines_data = self._parse_csv(file_content)
        elif self.file_name and self.file_name.lower().endswith(('.xls', '.xlsx')):
            if not xlrd:
                raise UserError(_("The 'xlrd' library is not installed on this server. Please use CSV format instead."))
            lines_data = self._parse_excel(file_content)
        else:
            try:
                lines_data = self._parse_csv(file_content)
            except:
                raise UserError(_("Unsupported file format. Please upload a .csv or .xls/.xlsx file."))

        if not lines_data:
            raise UserError(_("No data found in the uploaded file. Please ensure columns match the template."))

        self._create_checklist_lines(lines_data)
        
        return {'type': 'ir.actions.act_window_close'}

    def _parse_csv(self, content):
        data = []
        try:
            try:
                decoded_content = content.decode('utf-8')
            except UnicodeDecodeError:
                decoded_content = content.decode('latin1')
                
            stream = io.StringIO(decoded_content)
            reader = csv.DictReader(stream)
            for row in reader:
                if any(row.values()): # Skip empty rows
                    data.append(row)
        except Exception as e:
            raise UserError(_("Error parsing CSV: %s") % str(e))
        return data

    def _parse_excel(self, content):
        data = []
        try:
            book = xlrd.open_workbook(file_contents=content)
            sheet = book.sheet_by_index(0)
            headers = [str(sheet.cell_value(0, i)).strip() for i in range(sheet.ncols)]
            
            for row_idx in range(1, sheet.nrows):
                row_dict = {}
                has_value = False
                for col_idx in range(sheet.ncols):
                    header = headers[col_idx]
                    val = sheet.cell_value(row_idx, col_idx)
                    if val:
                        has_value = True
                    row_dict[header] = val
                if has_value:
                    data.append(row_dict)
        except Exception as e:
            raise UserError(_("Error parsing Excel: %s") % str(e))
        return data

    def _create_checklist_lines(self, rows):
        checklist_lines = []
        
        # Mapping for column names (to be flexible with headers)
        col_seq = ['Sequence', 'sequence', 'Seq', 'seq', 'Order', 'order']
        col_name = ['Item Name', 'name', 'Checklist Item', 'Item', 'Requirement', 'item_name']
        col_mandatory = ['Mandatory', 'mandatory', 'Required', 'required']

        def get_val(row, aliases):
            for alias in aliases:
                if alias in row:
                    return row[alias]
            return None

        for row in rows:
            name_val = get_val(row, col_name)
            if not name_val:
                continue

            seq_val = get_val(row, col_seq)
            try:
                sequence = int(float(seq_val)) if seq_val else 10
            except:
                sequence = 10

            mandatory_val = str(get_val(row, col_mandatory) or 'Yes').lower().strip()
            mandatory = mandatory_val in ('yes', 'true', '1', 'y')

            checklist_lines.append((0, 0, {
                'sequence': sequence,
                'name': str(name_val).strip(),
                'mandatory': mandatory,
            }))
        
        if checklist_lines:
            self.template_id.write({'line_ids': checklist_lines})

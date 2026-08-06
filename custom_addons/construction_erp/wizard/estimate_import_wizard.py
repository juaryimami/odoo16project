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

class ConstructionEstimateImportWizard(models.TransientModel):
    _name = 'construction.estimate.import.wizard'
    _description = 'Import Estimate Lines from Excel/CSV'

    estimate_id = fields.Many2one('construction.estimate', string='Estimate', required=True)
    file = fields.Binary(string='File Content')
    file_name = fields.Char(string='File Name')

    def action_download_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/construction/estimate_template',
            'target': 'new',
        }
    
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
            # Fallback attempt if file_name is missing but we want to try parsing
            try:
                lines_data = self._parse_csv(file_content)
            except:
                raise UserError(_("Unsupported file format. Please upload a .csv or .xls/.xlsx file."))

        if not lines_data:
            raise UserError(_("No data found in the uploaded file. Please ensure columns match the template."))

        self._create_estimate_lines(lines_data)
        
        self.estimate_id.message_post(body=_("<b>Bulk Import Successful</b><br/>Imported %s estimation lines from <i>%s</i>.") % (len(lines_data), self.file_name or 'file'))
        return {'type': 'ir.actions.act_window_close'}

    def _parse_csv(self, content):
        data = []
        try:
            # Attempt to handle different encodings
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

    def _create_estimate_lines(self, rows):
        estimate_lines = []
        created_products = []
        
        # Mapping for column names (to be flexible with headers)
        col_product = ['Product', 'product', 'Material', 'Item', 'Reference']
        col_type = ['Category', 'Type', 'type', 'category']
        col_qty = ['Quantity', 'Qty', 'qty', 'quantity', 'Amount']
        col_price = ['Unit Cost', 'Unit Price', 'Price', 'price', 'unit_price', 'Cost', 'cost']

        def get_val(row, aliases):
            for alias in aliases:
                if alias in row:
                    return row[alias]
            return None

        for row in rows:
            product_val = get_val(row, col_product)
            if not product_val:
                continue
                
            # Search for product by Name or Internal Reference
            product = self.env['product.product'].search([
                '|', ('name', '=', str(product_val).strip()), ('default_code', '=', str(product_val).strip())
            ], limit=1)
            
            type_val = str(get_val(row, col_type) or 'material').lower().strip()
            # Map user friendly names to internal keys
            type_mapping = {
                'material': 'material',
                'labor': 'labor',
                'labour': 'labor',
                'worker': 'labor',
                'equipment': 'equipment',
                'machine': 'equipment',
                'fleet': 'vehicle',
                'vehicle': 'vehicle',
                'truck': 'vehicle',
                'overhead': 'overhead',
                'admin': 'overhead',
                'other': 'overhead'
            }
            mapped_type = type_mapping.get(type_val, 'material')

            if not product:
                # Dynamic Odoo 16 fields configuration for missing product creation
                detailed_type = 'service'
                is_construction_material = False
                
                if mapped_type == 'material':
                    detailed_type = 'product'  # Storable Product in Odoo 16
                    is_construction_material = True
                elif mapped_type == 'equipment':
                    detailed_type = 'product'  # Storable Product in Odoo 16
                    is_construction_material = False
                elif mapped_type in ('labor', 'vehicle', 'overhead'):
                    detailed_type = 'service'  # Service Type
                    is_construction_material = False
                
                product_name = str(product_val).strip()
                
                # Check within the loop cache in case we import duplicate new products
                product = self.env['product.product'].search([
                    '|', ('name', '=', product_name), ('default_code', '=', product_name)
                ], limit=1)
                
                if not product:
                    product = self.env['product.product'].create({
                        'name': product_name,
                        'detailed_type': detailed_type,
                        'is_construction_material': is_construction_material,
                        'default_code': product_name,
                        'sale_ok': False,
                        'purchase_ok': True,
                    })
                    created_products.append(f"{product_name} ({type_val.capitalize()})")

            qty_val = get_val(row, col_qty) or 1.0
            price_val = get_val(row, col_price) or 0.0
            
            try:
                qty = float(qty_val)
                price = float(price_val)
            except:
                qty = 1.0
                price = 0.0

            estimate_lines.append((0, 0, {
                'product_id': product.id,
                'type': mapped_type,
                'quantity': qty,
                'unit_price': price,
            }))
        
        if estimate_lines:
            self.estimate_id.write({'line_ids': estimate_lines})
            
        if created_products:
            msg = _("<b>Auto-Created Products</b><br/>The following products were not found in the database and have been automatically created based on their imported categories:<br/>%s") % (", ".join(created_products))
            self.estimate_id.message_post(body=msg)

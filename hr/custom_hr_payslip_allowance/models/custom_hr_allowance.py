from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomHrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    rate = fields.Float("Rate", default=15)
    min_amount = fields.Float("Min Amount", default=600)
    is_taxable = fields.Boolean("Is Taxable")


class CustomHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        for payslip in self:
            amount = 0
            line_id = False
            contract_id = False
            category_id = False
            name = False
            code = False
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contracts for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            if not contract_ids:
                raise ValidationError(
                    _("No running contract found for the employee: %s or no contract in the given period" % payslip.employee_id.name))

            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            for index, line in enumerate(lines):
                line_dict = line[2]
                payslip_rule = self.env['hr.salary.rule'].search([('id', '=', line_dict['salary_rule_id'])], limit=1)
                if payslip_rule and payslip_rule.is_taxable:
                    if payslip_rule.min_amount < line_dict['amount']:
                        line_id = payslip_rule.id
                        contract_id = line_dict['contract_id']
                        category_id = line_dict['category_id']
                        name = line_dict['name'] + "(taxable)"
                        code = 'ALW'
                        amount = line_dict['amount'] - payslip_rule.min_amount
                        line_dict['amount'] = payslip_rule.min_amount
                        line_dict['name'] = line_dict['name'] + " (non-taxable)"
                        line_dict['code'] = 'NALW'
                    lines[index] = (0, 0, line_dict)

            if line_id and amount > 0:
                new_line_dict = {
                    'salary_rule_id': line_id,
                    'amount': amount,
                    'contract_id': contract_id,
                    'category_id': category_id,
                    'name': name,
                    'code': code,
                }
                lines.append((0, 0, new_line_dict))

            payslip.write({'line_ids': lines, 'number': number})
        return True

# from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError
#
#
# class CustomHrSalaryRule(models.Model):
#     _inherit = 'hr.salary.rule'
#     rate = fields.Float("Rate", default=15)
#     min_amount = fields.Float("Min Amount", default=600)
#     is_taxable = fields.Boolean("Is Taxable")
#
#
# class CustomHrPyslip(models.Model):
#     _inherit = 'hr.payslip'
#
#     def compute_sheet(self):
#         for payslip in self:
#             amount = 0
#             line_id = False
#             contract_id = False
#             category_id = False
#             name = False
#             code = False
#             number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
#             # delete old payslip lines
#             payslip.line_ids.unlink()
#             # set the list of contract for which the rules have to be applied
#             # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
#             contract_ids = payslip.contract_id.ids or \
#                            self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
#             if not contract_ids:
#                 raise ValidationError(
#                     _("No running contract found for the employee: %s or no contract in the given period" % payslip.employee_id.name))
#             lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
#             for index, line in enumerate(lines):
#                 line_dict = line[2]
#                 payslip_rule = self.env['hr.salary.rule'].search([('id', '=', line_dict['salary_rule_id'])], limit=1)
#                 if payslip_rule and payslip_rule.is_taxable:
#                     if payslip_rule.min_amount < line_dict['amount']:
#                         line_id = payslip_rule.id
#                         contract_id = line_dict['contract_id']
#                         category_id = line_dict['category_id']
#                         name = line_dict['name'] + "(taxable)"
#                         code = line_dict['code']
#                         amount = line_dict['amount'] - payslip_rule.min_amount
#                         line_dict['amount'] = payslip_rule.min_amount
#                         line_dict['name'] = line_dict['name']+" (none taxable)"
#
#                     lines[index] = (0, 0, line_dict)
#
#             if line_id and amount > 0:
#                 new_line_dict = {
#                     'salary_rule_id': line_id,  # Replace with the actual rule ID
#                     'amount': amount,  # Replace with the actual amount
#                     'contract_id': contract_id,  # Replace with the actual amount
#                     'category_id': category_id,  # Replace with the actual amount
#                     'name': name,  # Replace with the actual amount
#                     'code': code,  # Replace with the actual amount
#                 }
#                 lines.append((0, 0, new_line_dict))
#             payslip.write({'line_ids': lines, 'number': number})
#         return True

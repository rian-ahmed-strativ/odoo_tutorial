# from odoo import models, _
# from odoo.exceptions import UserError

# class EstateProperty(models.Model):
#     _inherit = 'estate.property'

#     def action_set_sold(self):
#         res = super().action_set_sold()

#         Invoice = self.env['account.move']
#         InvoiceLine = self.env['account.move.line']

#         for prop in self:
#             if not prop.partner_id:
#                 raise UserError(_("Cannot create invoice: no buyer specified for property %s") % prop.name)
#             invoice_vals = {
#                 'move_type': 'out_invoice',
#                 'partner_id': prop.partner_id.id,
#                 'invoice_origin': prop.name,
#                 'invoice_line_ids': [],
#             }
#             invoice = Invoice.create(invoice_vals)

#             line_vals = {
#                 'move_id': invoice.id,
#                 'name': _("Sale of %s") % prop.name,
#                 'quantity': 1,
#                 'price_unit': prop.selling_price,
#                 'account_id': self.env['ir.property']
#                     .get('property_account_income_categ_id', 'product.category')
#                     .id,
#             }
#             InvoiceLine.create(line_vals)
#             invoice.action_post()

#             prop.invoice_id = invoice.id

#         return res

# from odoo import models, fields, _
# from odoo.exceptions import UserError

# class EstateProperty(models.Model):
#     _inherit = 'estate.property'

#     invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)

#     def action_set_sold(self):

#         res = super().action_set_sold()

#         for prop in self:
#             if not prop.partner_id:
#                 raise UserError(_("Cannot create invoice - no buyer set for %s") % prop.name)

#             invoice = self.env['account.move'].create({
#                 'move_type': 'out_invoice',
#                 'partner_id': prop.partner_id.id,
#                 'invoice_origin': f"Property Sale: {prop.name}",
#                 'invoice_date': fields.Date.today(),
#             })

#             prop.invoice_id = invoice.id
#         return res

from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError

class EstateProperty(models.Model):
    _inherit = 'estate.property'
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    def action_set_sold(self):
        res = super().action_set_sold()
        
        for prop in self:
            if not prop.partner_id:
                raise UserError(_("Cannot create invoice: No buyer specified for %s") % prop.name)
            
            if not prop.selling_price or prop.selling_price <= 0:
                raise UserError(_("Cannot create invoice: Invalid selling price for %s") % prop.name)

            commission = prop.selling_price * 0.06
            admin_fee = 100.00

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': prop.partner_id.id,
                'invoice_origin': f"Property sale: {prop.name}",
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [
                    Command.create({
                        'name': f"Sales commission for {prop.name}",
                        'quantity': 1,
                        'price_unit': commission,
                        'account_id': self._get_default_income_account().id,
                    }),
                    Command.create({
                        'name': "Administrative fees",
                        'quantity': 1,
                        'price_unit': admin_fee,
                        'account_id': self._get_default_income_account().id,
                    })
                ]
            })
            
            prop.invoice_id = invoice.id
            
        return res

    def _get_default_income_account(self):
        """Helper method to get default income account"""
        return self.env['account.account'].search([
            ('user_type_id.type', '=', 'other'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
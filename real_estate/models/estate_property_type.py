from odoo import models, fields, api

class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Real Estate Property Type"
    _order = "sequence asc, name asc"  # This ensures proper ordering

    # Add the sequence field FIRST
    sequence = fields.Integer(
        string="Sequence",
        default=1,
        help="Drag and drop to reorder types (lower numbers show first)"
    )

    name = fields.Char(string="Name", required=True)
    property_ids = fields.One2many(
        'estate.property', 
        'property_type_id', 
        string='Properties'
    )
    property_count = fields.Integer(
        string="Properties Count",
        compute="_compute_property_count"
    )
    offer_ids = fields.One2many(
    "estate.property.offer",
    "property_type_id",
    string="Offers"
    )
    offer_count = fields.Integer(
    string="Offers Count",
    compute="_compute_offer_count"
    )
    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for prop_type in self:
            prop_type.offer_count = len(prop_type.offer_ids)
    def _compute_property_count(self):
        for prop_type in self:
            prop_type.property_count = self.env['estate.property'].search_count([
                ('property_type_id', '=', prop_type.id)
            ])

    _sql_constraints = [
        ('unique_property_type_name', 'UNIQUE(name)', 'The property type name must be unique.')
    ]
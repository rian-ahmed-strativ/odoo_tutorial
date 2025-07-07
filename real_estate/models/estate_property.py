from odoo import api, models, fields
from datetime import date, timedelta
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _order = 'id desc'

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False, default=lambda self: date.today() + timedelta(days=90), required= False)
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    total_area = fields.Float(
        string="Total Area (sqm)",
        compute="_compute_total_area",
        store=True
    )
    _sql_constraints = [
    ('check_expected_price_positive', 'CHECK(expected_price > 0)', 'The expected price must be strictly positive.'),
    ('check_selling_price_positive', 'CHECK(selling_price >= 0)', 'The selling price must be positive.'),
    ('unique_property_type_name', 'UNIQUE(name)', 'The property type name must be unique.')
    ]

    @api.depends('living_area', 'garden_area', 'garden')
    def _compute_total_area(self):
        for record in self:
            garden_area = record.garden_area if record.garden else 0
            record.total_area = record.living_area + garden_area

    best_offer = fields.Float(
    string="Best Offer",
    compute="_compute_best_offer",
    store=True,
    help="Highest offer received for this property"
    )
    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for property in self:
            if property.offer_ids:
                all_prices = property.offer_ids.mapped('price')
                property.best_offer = max(all_prices)
            else:
                property.best_offer = 0.0

    @api.onchange('garden')
    def _onchange_garden(self):
        """ Set garden area and orientation when garden is checked """
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    def action_set_sold(self):
        for record in self:
            if record.state == 'canceled':
                raise UserError("Canceled properties cannot be sold.")
            if not any(offer.status == 'accepted' for offer in record.offer_ids):
                raise UserError("Cannot sell a property without an accepted offer.")

            accepted_offer = record.offer_ids.filtered(lambda o: o.status == 'accepted')
            if accepted_offer:
                # Check selling price constraint before setting to sold
                selling_price = accepted_offer[0].price
                min_price = record.expected_price * 0.9
                if float_compare(selling_price, min_price, precision_digits=2) < 0:
                    raise UserError(
                        f"Cannot accept offer: The selling price ({selling_price:.2f}) is lower than 90% "
                        f"of the expected price ({min_price:.2f})."
                    )

                record.selling_price = selling_price
                record.partner_id = accepted_offer[0].partner_id

            record.state = 'sold'
        return True

    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise UserError("Sold properties cannot be canceled.")
            record.state = 'canceled'
            # Reset buyer and selling price when canceling
            record.partner_id = False
            record.selling_price = 0.0
        return True

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for property in self:
            if not float_is_zero(property.selling_price, precision_digits=2):
                min_price = property.expected_price * 0.9
                if float_compare(property.selling_price, min_price, precision_digits=2) < 0:
                    raise ValidationError(
                        f"The selling price ({property.selling_price:.2f}) cannot be lower than 90% of "
                        f"the expected price ({min_price:.2f})."
                    )

    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    garden_orientation = fields.Selection(
        string='Garden Orientation',
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ],
        help="Orientation of the garden."
    )
    active = fields.Boolean('Active', default=True)
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('canceled', 'Canceled'),
        ],
        required=True,
        copy=False,
        default='new'
    )
    status = fields.Selection(
        [('accepted', 'Accepted'),  # Must match exactly
        ('refused', 'Refused')],   # Must match exactly
        string="Status"
    )
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        index=True,
        tracking=True,
        default=lambda self: self.env.user
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Buyer',
        copy=False
    )
    tag_ids = fields.Many2many(
    'estate.property.tag',
    string='Tags'
)

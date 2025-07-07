from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "price desc"

    create_date = fields.Datetime(string="Creation Date", readonly=True, default=lambda self: fields.Datetime.now())
    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Date(
        string="Deadline",
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
        store=True
    )
    price = fields.Float(string="Price")
    status = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused')
    ], copy=False, string="Status")
    partner_id = fields.Many2one("res.partner", required=True, string="Partner")
    property_id = fields.Many2one("estate.property", required=True, string="Property")
    _sql_constraints = [
    ('check_price_positive', 'CHECK(price > 0)', 'The offer price must be strictly positive.')
    ]
    property_type_id = fields.Many2one(
    "estate.property.type",
    string="Property Type",
    related="property_id.property_type_id",
    store=True  # Make it stored to enable searching/filtering
)

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for offer in self:
            if offer.create_date:
                create_date = fields.Datetime.from_string(offer.create_date).date()
                offer.date_deadline = create_date + timedelta(days=offer.validity)
            else:
                offer.date_deadline = fields.Date.today() + timedelta(days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            if offer.date_deadline:
                if offer.create_date:
                    create_date = fields.Datetime.from_string(offer.create_date).date()
                    offer.validity = (offer.date_deadline - create_date).days
                else:
                    offer.validity = (offer.date_deadline - fields.Date.today()).days

    def action_accept_offer(self):
        for offer in self:
            property = offer.property_id

            if property.state == 'sold':
                raise UserError("Cannot accept an offer for a sold property.")

            accepted_offer = property.offer_ids.filtered(lambda o: o.status == 'accepted' and o.id != offer.id)
            if accepted_offer:
                raise UserError("Another offer has already been accepted for this property.")

            offer.status = 'accepted'
            property.write({
                'state': 'offer_accepted',
                'selling_price': offer.price,
                'partner_id': offer.partner_id.id
            })
        return True


    def action_refuse_offer(self):
        for offer in self:
            if offer.status == 'accepted':
                offer.property_id.write({
                    'state': 'offer_received',
                    'selling_price': 0,
                    'partner_id': False
                })
            offer.status = 'refused'
        return True
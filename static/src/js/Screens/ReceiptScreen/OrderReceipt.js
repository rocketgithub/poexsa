odoo.define('poexa.OrderReceipt', function (require) {
    "use strict";

    const { format } = require('web.field_utils');

    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

    const PoexaOrderReceipts = (OrderReceipt) =>
        class extends OrderReceipt {
            constructor() {
                super(...arguments);
            }

            async willStart() {
                const env = this.receiptEnv;
                console.log('ENV')
                console.log(env)
                console.log(this.env.pos.get_order().get_take_out_state())
                console.log(this.state)

            }
        };

    Registries.Component.extend(OrderReceipt, PoexaOrderReceipts);

});

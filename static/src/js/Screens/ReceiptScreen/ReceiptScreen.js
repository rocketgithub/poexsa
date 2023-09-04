odoo.define('poexsa.ReceiptScreen', function (require) {
    "use strict";

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const PoexsaReceiptScreen = (ReceiptScreen) =>
        class extends ReceiptScreen {
            async printReceipt() {
                super.printReceipt();
                if (this.env.pos.config.monitor == false){
                    this._printReceipt();
                }
            }
        };

    Registries.Component.extend(ReceiptScreen, PoexsaReceiptScreen);
});

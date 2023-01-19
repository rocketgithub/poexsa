odoo.define('poexsa.models', function (require) {
    'use strict';

    var models = require('point_of_sale.models');

    models.load_models([{
        model:  'decimal.precision',
        fields: ['name','digits'],
        loaded: function(self,dps){
            self.dp  = {};
            for (var i = 0; i < dps.length; i++) {
                self.dp[dps[i].name] = 2;
            }
        },
    }]);

    models.load_models([{
        model: 'res.currency',
        fields: ['name','symbol','position','rounding','rate'],
        ids:    function(self){ return [self.config.currency_id[0], self.company.currency_id[0]]; },
        loaded: function(self, currencies){
            currencies[0].decimals = 2
            currencies[0].rounding = 0.01
            self.currency = currencies[0];
            if (self.currency.rounding > 0 && self.currency.rounding < 1) {
                self.currency.decimals = Math.ceil(Math.log(1.0 / self.currency.rounding) / Math.log(10));
            } else {
                self.currency.decimals = 0;
            }

            currencies[1].decimals = 2
            currencies[1].rounding = 0.01
            self.company_currency = currencies[1];
        },


    }]);

});

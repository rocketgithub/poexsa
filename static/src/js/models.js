odoo.define('poexsa.models', function (require) {
    'use strict';

    var modelsgt = require('pos_gt.pos_gt');

    modelsgt.models.load_models([{
        model:  'decimal.precision',
        fields: ['name','digits'],
        loaded: function(self,dps){
            self.dp  = {};
            for (var i = 0; i < dps.length; i++) {
                self.dp[dps[i].name] = 2;
            }
        },
    }]);

    modelsgt.models.load_models([{
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

    var _super_order = modelsgt.models.Order.prototype;
    modelsgt.models.Order = modelsgt.models.Order.extend({
        initialize: function() {
          _super_order.initialize.apply(this,arguments);
          var uid_dividido = this.uid.split('-');
          this.take_out = true;
          this.nuevo_numero = parseInt(uid_dividido[1]) + parseInt(uid_dividido[2]);
        },
    })

});

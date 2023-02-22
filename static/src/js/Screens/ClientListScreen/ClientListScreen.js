odoo.define('poexsa.ClientListScreen', function (require) {
    'use strict';
    
    const Registries = require('point_of_sale.Registries');
    const ClientListScreen = require('point_of_sale.ClientListScreen')
    
    const PoexsaClientListScreen = ClientListScreen =>
    class extends ClientListScreen {
        async getNewClient() {
            let result = await super.getNewClient(event);
            let fields = _.find(this.env.pos.models, function(model){ return model.label === 'load_partners'; }).fields;
            if (!result.length) {
                result = await this.rpc({
                    model: 'res.partner',
                    method: 'obtener_cliente_nit_sat',
                    args: [[], [this.state.query, fields, this.env.pos.company.id]],
                }, {
                    timeout: 3000,
                    shadow: true,
                });
                
                if (result.length) {
                    this.state.selectedClient = result[0];
                    this.clickNext();
                } else {
                    await this.showPopup('ErrorPopup', {
                        title: 'NIT',
                        body: this.env._t('El NIT no fue encontrado'),
                    });
                }
            }
            return result;
        }
    };
    
    Registries.Component.extend(ClientListScreen, PoexsaClientListScreen);
    
    return PoexsaClientListScreen;
    
});

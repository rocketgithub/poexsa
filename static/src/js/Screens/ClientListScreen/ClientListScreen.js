odoo.define('poexsa.ClientListScreen', function (require) {
    'use strict';

    const { useState, useExternalListener } = owl.hooks;
    const { useListener } = require('web.custom_hooks');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ClientListScreen = require('point_of_sale.ClientListScreen')

    const PoexaClientListScreen = ClientListScreen =>
        class extends ClientListScreen {
          constructor(){
            super(...arguments);
          }
          async updateClientList(event) {
              var newClientList = await this.getNewClient();
              this.state.query = event.target.value;
              const clients = this.clients;
              if (event.code === 'Enter' && clients.length === 1) {
                  this.state.selectedClient = clients[0];
                  this.clickNext();
              } else if (event.code === 'Enter' && clients.length === 0){
                  var clientePorNitSat = await this.getClientePorNitSat();

                  if (clientePorNitSat){
                    var nuevoCliente = await this.getNewClient();
                    this.render();
                    if (nuevoCliente.length > 0){

                      this.state.selectedClient = nuevoCliente[0];
                      this.clickNext();
                    }

                  }
              }else {
                  this.render();
              }
          }
          async getClientePorNitSat(){
            var result = await this.rpc({
                model: 'res.partner',
                method: 'obtener_cliente_nit_sat',
                args: [[],[this.state.query,this.env.pos.company.id]],
            },{
                timeout: 3000,
                shadow: true,
            });
            return result

          }
          async getNewClient() {
              var domain = [];
              if(this.state.query) {
                  domain = [["vat", "ilike", this.state.query + "%"]];
              }
              var fields = _.find(this.env.pos.models, function(model){ return model.label === 'load_partners'; }).fields;
              var result = await this.rpc({
                  model: 'res.partner',
                  method: 'search_read',
                  args: [domain, fields],
                  kwargs: {
                      limit: 10,
                  },
              },{
                  timeout: 3000,
                  shadow: true,
              });
              return result;
          }

        };

    Registries.Component.extend(ClientListScreen, PoexaClientListScreen);

    return PoexaClientListScreen;


});

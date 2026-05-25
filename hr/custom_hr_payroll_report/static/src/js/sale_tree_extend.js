/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';

export class SaleListController extends ListController {
   setup() {
       super.setup();
   }
   OnTestClick() {
       var rpc =require('web.rpc');
        rpc.query({
          model:'sale.order.report',
          method:'refresh_report',
          args:[[]]
        });
       this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'sale.order.report',
          name:'Refresh',
          view_mode: 'tree',
          view_type: 'tree',
          views: [[false, 'tree']],
          target: 'current',
          res_id: false,
      });
   }
}
registry.category("views").add("button_in_tree", {
   ...listView,
   Controller: SaleListController,
   buttonTemplate: "button_sale.ListView.Buttons",
});

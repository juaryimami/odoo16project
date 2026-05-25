const xmlrpc = require('xmlrpc');
require('dotenv').config();

const url = new URL(process.env.ODOO_URL || 'http://localhost:8060');
const common = xmlrpc.createClient({ host: url.hostname, port: url.port, path: '/xmlrpc/2/common' });
const models = xmlrpc.createClient({ host: url.hostname, port: url.port, path: '/xmlrpc/2/object' });

const db = process.env.ODOO_DB || 'test16_prod';
const user = process.env.ODOO_USER || 'admin';
const pass = process.env.ODOO_PASSWORD || 'test16_Super_Admin_Pass';

common.methodCall('authenticate', [db, user, pass, {}], (err, uid) => {
  if (err || !uid) return console.log(err || 'Auth failed');
  models.methodCall('execute_kw', [db, uid, pass, 'sale.order', 'fields_get', [], { attributes: ['string', 'type'] }], (err, fields) => {
    if (err) return console.log(err);
    const keys = Object.keys(fields);
    console.log("Fields containing 'opp':", keys.filter(k => k.includes('opp')));
    console.log("Fields containing 'lead':", keys.filter(k => k.includes('lead')));
    console.log("Fields containing 'campaign':", keys.filter(k => k.includes('campaign')));
    console.log("Fields containing 'tag':", keys.filter(k => k.includes('tag')));
    console.log("Fields containing 'source':", keys.filter(k => k.includes('source')));
  });
});

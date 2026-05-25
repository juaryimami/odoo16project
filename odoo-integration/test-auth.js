const xmlrpc = require('xmlrpc');
require('dotenv').config();

const odooConfig = {
  url: 'http://localhost:8060',
  db: 'construction',
  user: 'juharyimer7@gmail.com',
  password: 'odoo'
};

async function testAuth() {
  console.log('Testing Odoo authentication for:', odooConfig.user);
  console.log('URL:', odooConfig.url);
  console.log('DB:', odooConfig.db);

  const url = new URL(odooConfig.url);
  const commonClient = xmlrpc.createClient({
    host: url.hostname,
    port: url.port,
    path: '/xmlrpc/2/common'
  });

  commonClient.methodCall('authenticate', [
    odooConfig.db,
    odooConfig.user,
    odooConfig.password,
    {}
  ], (err, uid) => {
    if (err) {
      console.error('❌ Authentication error:', err);
    } else if (uid) {
      console.log('✅ Authentication successful! UID:', uid);
    } else {
      console.error('❌ Authentication failed: Invalid credentials or database name.');
    }
  });
}

testAuth();

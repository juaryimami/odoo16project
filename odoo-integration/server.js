const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const xmlrpc = require('xmlrpc');
const cron = require('node-cron');
const { bulkSync } = require('./bulk-sync');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 9098;

app.use(cors());
app.use(bodyParser.json());

// Odoo Configuration from .env
const odooConfig = {
  url: process.env.ODOO_URL || 'http://localhost:8060',
  db: process.env.ODOO_DB || 'test16_prod',
  user: process.env.ODOO_USER || 'admin',
  password: process.env.ODOO_PASSWORD || 'test16_Super_Admin_Pass'
};

// Helper: Perform XML-RPC calls to Odoo
const executeKw = async (model, method, args, kwargs = {}) => {
  const url = new URL(odooConfig.url);
  const commonClient = xmlrpc.createClient({
    host: url.hostname,
    port: url.port,
    path: '/xmlrpc/2/common'
  });

  return new Promise((resolve, reject) => {
    // 1. Authenticate
    commonClient.methodCall('authenticate', [
      odooConfig.db,
      odooConfig.user,
      odooConfig.password,
      {}
    ], (err, uid) => {
      if (err) return reject(err);
      if (!uid) return reject(new Error('Authentication failed'));

      // 2. Execute Method
      const objectClient = xmlrpc.createClient({
        host: url.hostname,
        port: url.port,
        path: '/xmlrpc/2/object'
      });

      objectClient.methodCall('execute_kw', [
        odooConfig.db,
        uid,
        odooConfig.password,
        model,
        method,
        args,
        kwargs
      ], (err, result) => {
        if (err) return reject(err);
        resolve(result);
      });
    });
  });
};

/**
 * Endpoint: POST /sync-patient
 * Payload can be a direct patient object OR a Hasura Event Trigger payload
 */
app.post('/sync-patient', async (req, res) => {
  try {
    console.log('Received sync request:', JSON.stringify(req.body, null, 2));

    // Handle Hasura Event Trigger structure or direct payload
    let patientData = req.body;
    if (req.body.event && req.body.event.data && req.body.event.data.new) {
      patientData = req.body.event.data.new;
    }

    if (!patientData.name) {
      return res.status(400).json({ error: 'Patient name is required' });
    }

    // Prepare data for Odoo res.partner
    const partnerData = {
      name: patientData.name,
      phone: patientData.phone || '',
      email: patientData.email || '',
      ref: patientData.orbit_id || '',
      comment: `EMR Patient ID: ${patientData.id || 'N/A'}\nOrbit ID: ${patientData.orbit_id || 'N/A'}`,
      customer_rank: 1, // Make them a customer in Odoo 16+
      is_company: false,
      type: 'contact',
    };

    // Optionally map date_of_birth if your Odoo has the field or use comment
    if (patientData.date_of_birth) {
      partnerData.comment += `\nDOB: ${patientData.date_of_birth}`;
    }

    console.log('Syncing to Odoo as res.partner:', partnerData);

    let odooPartnerId;
    try {
      // 1. Search for existing partner by ref (Orbit ID)
      const existingPartners = await executeKw('res.partner', 'search_read', [
        [['ref', '=', partnerData.ref]],
        ['id']
      ]);

      if (existingPartners && existingPartners.length > 0) {
        odooPartnerId = existingPartners[0].id;
        console.log(`Found existing partner (ID: ${odooPartnerId}). Updating...`);
        await executeKw('res.partner', 'write', [[odooPartnerId], partnerData]);
      } else {
        console.log('No existing partner found. Creating new...');
        odooPartnerId = await executeKw('res.partner', 'create', [[partnerData]]);
      }

      console.log('✅ Successfully synced to Odoo. Partner ID:', odooPartnerId);

      res.json({
        success: true,
        odoo_partner_id: odooPartnerId,
        message: 'Patient synced to Odoo CRM successfully'
      });
    } catch (innerError) {
      throw innerError;
    }

  } catch (error) {
    console.error('❌ Sync failed:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Health Check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'odoo-integration' });
});

// Schedule Daily Bulk Sync at 1:00 AM
cron.schedule('0 1 * * *', async () => {
    console.log(`[${new Date().toISOString()}] 📅 Triggering scheduled daily bulk sync...`);
    try {
        await bulkSync();
    } catch (err) {
        console.error(`[${new Date().toISOString()}] ❌ Scheduled bulk sync failed:`, err.message);
    }
});

app.listen(port, () => {
  console.log(`🚀 Odoo Integration Service listening at http://localhost:${port}`);
  console.log(`📅 Daily bulk sync scheduled for 1:00 AM.`);
});

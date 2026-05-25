const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const xmlrpc = require('xmlrpc');
const cron = require('node-cron');
const { Pool } = require('pg');
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

// PostgreSQL Pool for lookups
const pool = new Pool({
  connectionString: process.env.POSTGRES_URI || 'postgres://postgres:postgres@localhost:5432/orbit_3_patient',
});

const imagingPool = new Pool({
  connectionString: process.env.IMAGING_POSTGRES_URI || 'postgres://postgres:postgres@localhost:5432/orbit_3_imaging',
});

// Helper: Format Date for Odoo (YYYY-MM-DD HH:MM:SS)
const formatDateToOdoo = (dateStr) => {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  return d.toISOString().replace('T', ' ').substring(0, 19);
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

    // Resolve patient_source_id to an Odoo Tag (category_id)
    let odooTagIds = [];
    if (patientData.patient_source_id) {
      try {
        const sourceRes = await pool.query('SELECT name FROM duplicate.patient_sources WHERE id = $1', [patientData.patient_source_id]);
        if (sourceRes.rows.length > 0) {
          const sourceName = sourceRes.rows[0].name;
          
          // Search Odoo for existing tag
          const existingTags = await executeKw('res.partner.category', 'search_read', [
            [['name', '=', sourceName]],
            ['id']
          ]);
          
          if (existingTags && existingTags.length > 0) {
            odooTagIds.push(existingTags[0].id);
          } else {
            // Create the tag in Odoo
            const newTagId = await executeKw('res.partner.category', 'create', [{ name: sourceName }]);
            odooTagIds.push(newTagId);
          }
        }
      } catch (err) {
        console.error('❌ Error resolving patient source tag:', err.message);
      }
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

    if (odooTagIds.length > 0) {
      partnerData.category_id = [[6, 0, odooTagIds]];
    }

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

/**
 * Endpoint: POST /sync-referer
 */
app.post('/sync-referer', async (req, res) => {
  try {
    let refererData = req.body;
    if (req.body.event && req.body.event.data && req.body.event.data.new) {
      refererData = req.body.event.data.new;
    }

    if (!refererData.full_name) {
      return res.status(400).json({ error: 'Referer full_name is required' });
    }

    const leadData = {
      name: `Referer - ${refererData.full_name}`,
      contact_name: refererData.full_name,
      phone: refererData.phone_number || '',
      description: `Speciality: ${refererData.speciality || 'N/A'}\nOther: ${refererData.other || 'N/A'}\nOrbit ID: ${refererData.id}`,
      type: 'lead',
    };

    let odooLeadId;
    const existingLeads = await executeKw('crm.lead', 'search_read', [
      [['description', 'ilike', `%Orbit ID: ${refererData.id}%`]],
      ['id']
    ]);

    if (existingLeads && existingLeads.length > 0) {
      odooLeadId = existingLeads[0].id;
      await executeKw('crm.lead', 'write', [[odooLeadId], leadData]);
    } else {
      odooLeadId = await executeKw('crm.lead', 'create', [[leadData]]);
    }

    res.json({ success: true, odoo_lead_id: odooLeadId, message: 'Referer synced to Odoo CRM successfully' });
  } catch (error) {
    console.error('❌ Sync failed:', error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * Endpoint: POST /sync-referer-institution
 */
app.post('/sync-referer-institution', async (req, res) => {
  try {
    let institutionData = req.body;
    if (req.body.event && req.body.event.data && req.body.event.data.new) {
      institutionData = req.body.event.data.new;
    }

    if (!institutionData.name) {
      return res.status(400).json({ error: 'Institution name is required' });
    }

    const leadData = {
      name: `Institution - ${institutionData.name}`,
      partner_name: institutionData.name,
      description: `Description: ${institutionData.description || 'N/A'}\nOrbit ID: ${institutionData.id}`,
      type: 'lead',
    };

    let odooLeadId;
    const existingLeads = await executeKw('crm.lead', 'search_read', [
      [['description', 'ilike', `%Orbit ID: ${institutionData.id}%`]],
      ['id']
    ]);

    if (existingLeads && existingLeads.length > 0) {
      odooLeadId = existingLeads[0].id;
      await executeKw('crm.lead', 'write', [[odooLeadId], leadData]);
    } else {
      odooLeadId = await executeKw('crm.lead', 'create', [[leadData]]);
    }

    res.json({ success: true, odoo_lead_id: odooLeadId, message: 'Referer Institution synced to Odoo CRM successfully' });
  } catch (error) {
    console.error('❌ Sync failed:', error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * Endpoint: POST /sync-imaging-service
 */
app.post('/sync-imaging-service', async (req, res) => {
  try {
    let serviceData = req.body;
    if (req.body.event && req.body.event.data && req.body.event.data.new) {
      serviceData = req.body.event.data.new;
    }

    if (!serviceData.code) {
      return res.status(400).json({ error: 'Service code is required' });
    }

    const productData = {
      name: serviceData.custom_name || serviceData.description || serviceData.code,
      type: 'service',
      list_price: serviceData.price || 0.0,
      default_code: serviceData.code,
    };

    let odooProductId;
    const existingProducts = await executeKw('product.product', 'search_read', [
      [['default_code', '=', serviceData.code]],
      ['id']
    ]);

    if (existingProducts && existingProducts.length > 0) {
      odooProductId = existingProducts[0].id;
      await executeKw('product.product', 'write', [[odooProductId], productData]);
    } else {
      odooProductId = await executeKw('product.product', 'create', [[productData]]);
    }

    res.json({ success: true, odoo_product_id: odooProductId, message: 'Imaging Service synced to Odoo Product successfully' });
  } catch (error) {
    console.error('❌ Sync failed:', error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * Endpoint: POST /sync-imaging-order
 */
app.post('/sync-imaging-order', async (req, res) => {
  try {
    let orderData = req.body;
    if (req.body.event && req.body.event.data && req.body.event.data.new) {
      orderData = req.body.event.data.new;
    }

    if (!orderData.number) {
      return res.status(400).json({ error: 'Order number is required' });
    }

    // Lookup Patient (partner_id)
    let partnerId = false;
    if (orderData.patient_id) {
      const patientRes = await pool.query('SELECT orbit_id FROM patient.patients WHERE id = $1', [orderData.patient_id]);
      if (patientRes.rows.length > 0) {
        const orbitId = patientRes.rows[0].orbit_id;
        const existingPartners = await executeKw('res.partner', 'search_read', [[['ref', '=', orbitId]], ['id']]);
        if (existingPartners && existingPartners.length > 0) partnerId = existingPartners[0].id;
      }
    }

    // Lookup Lead/Referer to use as a Tag on the Sale Order (since opportunity_id doesn't exist)
    let odooTagIds = [];
    let refererOrbitId = orderData.referer_id || orderData.referer_institution_id;
    if (refererOrbitId) {
       const existingLeads = await executeKw('crm.lead', 'search_read', [[['description', 'ilike', `%Orbit ID: ${refererOrbitId}%`]], ['name']]);
       if (existingLeads && existingLeads.length > 0) {
         const refererName = `Referer: ${existingLeads[0].name}`;
         
         // Search or create a tag for this referer
         const existingTags = await executeKw('crm.tag', 'search_read', [[['name', '=', refererName]], ['id']]);
         if (existingTags && existingTags.length > 0) {
           odooTagIds.push(existingTags[0].id);
         } else {
           const newTagId = await executeKw('crm.tag', 'create', [{ name: refererName }]);
           odooTagIds.push(newTagId);
         }
       }
    }

    const saleOrderData = {
      client_order_ref: orderData.number,
    };
    
    const formattedDate = formatDateToOdoo(orderData.expected_date || orderData.created_at);
    if (formattedDate) {
      saleOrderData.date_order = formattedDate;
    }

    if (partnerId) saleOrderData.partner_id = partnerId;
    if (odooTagIds.length > 0) saleOrderData.tag_ids = [[6, 0, odooTagIds]];

    let odooSaleOrderId;
    const existingOrders = await executeKw('sale.order', 'search_read', [
      [['client_order_ref', '=', orderData.number]],
      ['id']
    ]);

    if (existingOrders && existingOrders.length > 0) {
      odooSaleOrderId = existingOrders[0].id;
      await executeKw('sale.order', 'write', [[odooSaleOrderId], saleOrderData]);
    } else {
      if (!partnerId) {
        return res.status(400).json({ success: false, error: 'Cannot create Sale Order without a synced Patient (partner_id)' });
      }
      odooSaleOrderId = await executeKw('sale.order', 'create', [[saleOrderData]]);
    }

    res.json({ success: true, odoo_sale_order_id: odooSaleOrderId, message: 'Imaging Order synced to Odoo Sale Order successfully' });
  } catch (error) {
    console.error('❌ Sync failed:', error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * Endpoint: POST /sync-imaging-order-item
 */
app.post('/sync-imaging-order-item', async (req, res) => {
  try {
    let itemData = req.body;
    if (req.body.event && req.body.event.data && req.body.event.data.new) {
      itemData = req.body.event.data.new;
    }

    if (!itemData.order_id || !itemData.service_id) {
      return res.status(400).json({ error: 'order_id and service_id are required' });
    }

    // 1. Get the order number from imaging.orders
    const orderRes = await imagingPool.query('SELECT number FROM imaging.orders WHERE id = $1', [itemData.order_id]);
    if (orderRes.rows.length === 0) return res.status(404).json({ error: 'Order not found in EMR' });
    const orderNumber = orderRes.rows[0].number;

    // 2. Find the sale.order in Odoo
    const existingOrders = await executeKw('sale.order', 'search_read', [[['client_order_ref', '=', orderNumber]], ['id']]);
    if (!existingOrders || existingOrders.length === 0) return res.status(404).json({ error: 'Sale Order not found in Odoo' });
    const saleOrderId = existingOrders[0].id;

    // 3. Get the service code and price from imaging.services
    const serviceRes = await imagingPool.query('SELECT code, price FROM imaging.services WHERE id = $1', [itemData.service_id]);
    if (serviceRes.rows.length === 0) return res.status(404).json({ error: 'Service not found in EMR' });
    const serviceCode = serviceRes.rows[0].code;
    const servicePrice = serviceRes.rows[0].price || 0.0;

    // 4. Find the product in Odoo
    const existingProducts = await executeKw('product.product', 'search_read', [[['default_code', '=', serviceCode]], ['id']]);
    if (!existingProducts || existingProducts.length === 0) return res.status(404).json({ error: 'Product not found in Odoo' });
    const productId = existingProducts[0].id;

    const existingLines = await executeKw('sale.order.line', 'search_read', [
      [['order_id', '=', saleOrderId], ['name', 'ilike', `%Orbit Item ID: ${itemData.id}%`]],
      ['id']
    ]);

    const lineData = {
      order_id: saleOrderId,
      product_id: productId,
      price_unit: servicePrice,
      product_uom_qty: 1,
      name: `Orbit Item ID: ${itemData.id}`,
    };

    if (existingLines && existingLines.length > 0) {
      await executeKw('sale.order.line', 'write', [[existingLines[0].id], lineData]);
    } else {
      await executeKw('sale.order.line', 'create', [[lineData]]);
    }

    res.json({ success: true, message: 'Imaging Order Item synced to Odoo Sale Order Line successfully' });
  } catch (error) {
    console.error('❌ Sync failed:', error.message);
    res.status(500).json({ success: false, error: error.message });
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

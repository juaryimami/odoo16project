const { Pool } = require('pg');
const axios = require('axios');
require('dotenv').config();

const pool = new Pool({
    connectionString: process.env.POSTGRES_URI || 'postgres://postgres:postgres@localhost:5432/orbit_3_patient',
});

const facilityPool = new Pool({
    connectionString: process.env.FACILITY_POSTGRES_URI || 'postgres://postgres:postgres@localhost:5432/orbit_3_facility',
});

const imagingPool = new Pool({
    connectionString: process.env.IMAGING_POSTGRES_URI || 'postgres://postgres:postgres@localhost:5432/orbit_3_imaging',
});

async function bulkSync() {
    console.log(`[${new Date().toISOString()}] 🔄 Starting scheduled bulk sync...`);

    try {
        // --- 1. Sync Patients ---
        const query = `
            SELECT id, name, phone, orbit_id, date_of_birth, sex, patient_source_id 
            FROM patient.patients 
            WHERE deleted_at IS NULL
        `;

        const res = await pool.query(query);
        const patients = res.rows;
        console.log(`[${new Date().toISOString()}] 🔍 Found ${patients.length} patients to sync.`);

        for (let i = 0; i < patients.length; i++) {
            const patient = patients[i];
            
            try {
                const response = await axios.post('http://localhost:9098/sync-patient', patient);
                if (!response.data.success) {
                    console.error(`   ❌ Failed to sync ${patient.name} (${patient.orbit_id}): ${response.data.error}`);
                }
            } catch (err) {
                console.error(`   ❌ Error calling sync service for ${patient.name}: ${err.message}`);
            }

            // Optional: Add a small delay to prevent overwhelming the Odoo XML-RPC
            await new Promise(resolve => setTimeout(resolve, 50));
        }

        // --- 2. Sync Referers ---
        const refererQuery = `
            SELECT id, full_name, speciality, phone_number, other 
            FROM basic.referers
        `;
        const refererRes = await facilityPool.query(refererQuery);
        const referers = refererRes.rows;
        console.log(`[${new Date().toISOString()}] 🔍 Found ${referers.length} referers to sync.`);

        for (let i = 0; i < referers.length; i++) {
            const referer = referers[i];
            try {
                const response = await axios.post('http://localhost:9098/sync-referer', referer);
                if (!response.data.success) {
                    console.error(`   ❌ Failed to sync Referer ${referer.full_name} (${referer.id}): ${response.data.error}`);
                }
            } catch (err) {
                console.error(`   ❌ Error calling sync service for Referer ${referer.full_name}: ${err.message}`);
            }
            await new Promise(resolve => setTimeout(resolve, 50));
        }

        // --- 3. Sync Referer Institutions ---
        const institutionQuery = `
            SELECT id, name, description 
            FROM basic.referer_institutions
        `;
        const institutionRes = await facilityPool.query(institutionQuery);
        const institutions = institutionRes.rows;
        console.log(`[${new Date().toISOString()}] 🔍 Found ${institutions.length} referer institutions to sync.`);

        for (let i = 0; i < institutions.length; i++) {
            const institution = institutions[i];
            try {
                const response = await axios.post('http://localhost:9098/sync-referer-institution', institution);
                if (!response.data.success) {
                    console.error(`   ❌ Failed to sync Institution ${institution.name} (${institution.id}): ${response.data.error}`);
                }
            } catch (err) {
                console.error(`   ❌ Error calling sync service for Institution ${institution.name}: ${err.message}`);
            }
            await new Promise(resolve => setTimeout(resolve, 50));
        }

        // --- 4. Sync Imaging Services ---
        const servicesQuery = `
            SELECT id, code, custom_name, description, price 
            FROM imaging.services 
            WHERE deleted_at IS NULL
        `;
        const servicesRes = await imagingPool.query(servicesQuery);
        console.log(`[${new Date().toISOString()}] 🔍 Found ${servicesRes.rowCount} imaging services to sync.`);
        
        for (const service of servicesRes.rows) {
            try {
                await axios.post('http://localhost:8080/sync-imaging-service', service);
            } catch (err) {
                console.error(`[Sync] Failed to sync service ${service.code}:`, err.message);
            }
        }

        // --- 5. Sync Imaging Orders ---
        const ordersQuery = `
            SELECT id, number, expected_date, created_at, patient_id, referer_id, referer_institution_id
            FROM imaging.orders 
        `;
        const ordersRes = await imagingPool.query(ordersQuery);
        console.log(`[${new Date().toISOString()}] 🔍 Found ${ordersRes.rowCount} imaging orders to sync.`);
        
        for (const order of ordersRes.rows) {
            try {
                await axios.post('http://localhost:8080/sync-imaging-order', order);
            } catch (err) {
                console.error(`[Sync] Failed to sync order ${order.number}:`, err.message);
            }
        }

        // --- 6. Sync Imaging Order Items ---
        const orderItemsQuery = `
            SELECT id, order_id, service_id
            FROM imaging.order_items 
        `;
        const orderItemsRes = await imagingPool.query(orderItemsQuery);
        console.log(`[${new Date().toISOString()}] 🔍 Found ${orderItemsRes.rowCount} imaging order items to sync.`);
        
        for (const item of orderItemsRes.rows) {
            try {
                await axios.post('http://localhost:8080/sync-imaging-order-item', item);
            } catch (err) {
                console.error(`[Sync] Failed to sync order item ${item.id}:`, err.message);
            }
        }

        console.log(`[${new Date().toISOString()}] ✅ Scheduled bulk sync completed.`);
    } catch (err) {
        console.error(`[${new Date().toISOString()}] ❌ Database connection error during bulk sync:`, err.stack);
    } finally {
        await client.end();
        await facilityClient.end();
    }
}

// Export the function for use in server.js
module.exports = { bulkSync };

// Allow direct execution if run via 'node bulk-sync.js'
if (require.main === module) {
    bulkSync();
}

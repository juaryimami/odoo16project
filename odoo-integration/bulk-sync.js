const { Client } = require('pg');
const axios = require('axios');
require('dotenv').config();

// Database connection details (from orbit-3-patient/.env)
const connectionString = process.env.POSTGRES_URI || 'postgres://postgres:postgres@localhost:5432/orbit_3_patient';

async function bulkSync() {
    console.log(`[${new Date().toISOString()}] 🔄 Starting scheduled bulk sync...`);
    const client = new Client({ connectionString });

    try {
        await client.connect();
        
        // Fetch all patients with their basic info
        const query = `
            SELECT id, name, phone, orbit_id, date_of_birth, sex 
            FROM patient.patients 
            WHERE deleted_at IS NULL
        `;

        const res = await client.query(query);
        const patients = res.rows;
        console.log(`[${new Date().toISOString()}] 🔍 Found ${patients.length} patients to sync.`);

        for (let i = 0; i < patients.length; i++) {
            const patient = patients[i];
            
            try {
                const response = await axios.post('http://localhost:9098/sync-patient', patient);
                // We don't log success for every record in bulk to keep logs clean,
                // but you can enable it for debugging.
                if (!response.data.success) {
                    console.error(`   ❌ Failed to sync ${patient.name} (${patient.orbit_id}): ${response.data.error}`);
                }
            } catch (err) {
                console.error(`   ❌ Error calling sync service for ${patient.name}: ${err.message}`);
            }

            // Optional: Add a small delay to prevent overwhelming the Odoo XML-RPC
            await new Promise(resolve => setTimeout(resolve, 50));
        }

        console.log(`[${new Date().toISOString()}] ✅ Scheduled bulk sync completed.`);
    } catch (err) {
        console.error(`[${new Date().toISOString()}] ❌ Database connection error during bulk sync:`, err.stack);
    } finally {
        await client.end();
    }
}

// Export the function for use in server.js
module.exports = { bulkSync };

// Allow direct execution if run via 'node bulk-sync.js'
if (require.main === module) {
    bulkSync();
}

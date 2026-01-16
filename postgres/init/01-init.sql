-- Crear schema para clientes
CREATE SCHEMA IF NOT EXISTS clients;

-- Función para crear tablas de clientes
CREATE OR REPLACE FUNCTION create_client_table(client_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS clients.%I (
            id SERIAL PRIMARY KEY,
            amount NUMERIC(12,2) NOT NULL,
            status VARCHAR(20) DEFAULT ''pending'',
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        )', client_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_status ON clients.%I(status)', client_name, client_name);
END;
$$ LANGUAGE plpgsql;

-- Crear 10 clientes
SELECT create_client_table('acme_corp');
SELECT create_client_table('tech_solutions');
SELECT create_client_table('global_services');
SELECT create_client_table('innovatech');
SELECT create_client_table('dataflow_inc');
SELECT create_client_table('cloud_systems');
SELECT create_client_table('netwise');
SELECT create_client_table('securepay');
SELECT create_client_table('fasttrack_logistics');
SELECT create_client_table('greentech_energy');

-- Función para poblar datos
CREATE OR REPLACE FUNCTION populate_client_data(client_name TEXT, num_records INT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        INSERT INTO clients.%I (amount, status, category, created_at)
        SELECT 
            (random() * 10000)::numeric(12,2),
            (ARRAY[''pending'', ''completed'', ''failed''])[1 + floor(random() * 3)::int],
            (ARRAY[''sales'', ''refund'', ''subscription''])[1 + floor(random() * 3)::int],
            NOW() - (random() * interval ''90 days'')
        FROM generate_series(1, %s)
    ', client_name, num_records);
END;
$$ LANGUAGE plpgsql;

-- Poblar datos iniciales
SELECT populate_client_data('acme_corp', 5000);
SELECT populate_client_data('tech_solutions', 3500);
SELECT populate_client_data('global_services', 8000);
SELECT populate_client_data('innovatech', 2000);
SELECT populate_client_data('dataflow_inc', 6000);
SELECT populate_client_data('cloud_systems', 4500);
SELECT populate_client_data('netwise', 1500);
SELECT populate_client_data('securepay', 7000);
SELECT populate_client_data('fasttrack_logistics', 3000);
SELECT populate_client_data('greentech_energy', 2500);

# Monitoring Stack

Prometheus + Grafana + PostgreSQL monitoring

## Contenido

- [Quick Start con Docker](#quick-start-con-docker)
- [Instalación sin Docker (Producción)](#instalación-sin-docker-producción)
- [Configurar conexión a DB real](#configurar-conexión-a-db-real)

---

## Quick Start con Docker

```bash
docker-compose up -d
```

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Grafana | http://localhost:3000 | admin / grafana_admin_2024 |
| Prometheus | http://localhost:9090 | - |

---

## Instalación sin Docker (Producción)

### Requisitos

- Windows Server / Linux / macOS
- PostgreSQL accesible en la red
- Puertos disponibles: 9090 (Prometheus), 9100 (node_exporter), 9187 (postgres_exporter), 3000 (Grafana)

---

### Paso 1: Instalar Node Exporter (métricas de hardware)

#### Linux

```bash
# Descargar
cd /tmp
curl -LO https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz

# Instalar
sudo mv node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter

# Crear servicio
sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Iniciar
sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter

# Verificar
curl http://localhost:9100/metrics
```

#### Windows Server

Usar **windows_exporter** en lugar de node_exporter:

```powershell
# Descargar desde https://github.com/prometheus-community/windows_exporter/releases
# Ejemplo: windows_exporter-0.25.1-amd64.msi

# Instalar como servicio
msiexec /i windows_exporter-0.25.1-amd64.msi

# Verificar
curl http://localhost:9182/metrics
```

> **Nota:** En Windows el puerto es 9182, no 9100.

---

### Paso 2: Instalar Postgres Exporter (métricas de PostgreSQL)

#### Linux

```bash
# Descargar
cd /tmp
curl -LO https://github.com/prometheus-community/postgres_exporter/releases/download/v0.15.0/postgres_exporter-0.15.0.linux-amd64.tar.gz
tar xvfz postgres_exporter-0.15.0.linux-amd64.tar.gz

# Instalar
sudo mv postgres_exporter-0.15.0.linux-amd64/postgres_exporter /usr/local/bin/
sudo useradd -rs /bin/false postgres_exporter

# Crear archivo de entorno con conexión a DB
sudo mkdir -p /etc/postgres_exporter
sudo tee /etc/postgres_exporter/postgres_exporter.env > /dev/null <<EOF
DATA_SOURCE_NAME=postgresql://USUARIO:PASSWORD@HOST:5432/DATABASE?sslmode=disable
EOF
sudo chmod 600 /etc/postgres_exporter/postgres_exporter.env

# Copiar queries.yml (desde este repo)
sudo cp prometheus/queries.yml /etc/postgres_exporter/queries.yml

# Crear servicio
sudo tee /etc/systemd/system/postgres_exporter.service > /dev/null <<EOF
[Unit]
Description=Postgres Exporter
After=network.target

[Service]
User=postgres_exporter
EnvironmentFile=/etc/postgres_exporter/postgres_exporter.env
ExecStart=/usr/local/bin/postgres_exporter --extend.query-path=/etc/postgres_exporter/queries.yml

[Install]
WantedBy=multi-user.target
EOF

# Iniciar
sudo systemctl daemon-reload
sudo systemctl enable postgres_exporter
sudo systemctl start postgres_exporter

# Verificar
curl http://localhost:9187/metrics
```

#### Windows Server

```powershell
# Descargar desde https://github.com/prometheus-community/postgres_exporter/releases
# Extraer postgres_exporter.exe a C:\postgres_exporter\

# Crear archivo de configuración
# C:\postgres_exporter\config.env
# DATA_SOURCE_NAME=postgresql://USUARIO:PASSWORD@HOST:5432/DATABASE?sslmode=disable

# Copiar queries.yml a C:\postgres_exporter\queries.yml

# Instalar como servicio con NSSM (descargar de https://nssm.cc/)
nssm install postgres_exporter "C:\postgres_exporter\postgres_exporter.exe"
nssm set postgres_exporter AppParameters "--extend.query-path=C:\postgres_exporter\queries.yml"
nssm set postgres_exporter AppEnvironmentExtra "DATA_SOURCE_NAME=postgresql://USUARIO:PASSWORD@HOST:5432/DATABASE?sslmode=disable"

# Iniciar
nssm start postgres_exporter

# Verificar
curl http://localhost:9187/metrics
```

---

### Paso 3: Instalar Prometheus

#### Linux

```bash
# Descargar
cd /tmp
curl -LO https://github.com/prometheus/prometheus/releases/download/v2.50.1/prometheus-2.50.1.linux-amd64.tar.gz
tar xvfz prometheus-2.50.1.linux-amd64.tar.gz

# Instalar
sudo mv prometheus-2.50.1.linux-amd64 /opt/prometheus
sudo useradd -rs /bin/false prometheus
sudo chown -R prometheus:prometheus /opt/prometheus

# Crear directorio de datos
sudo mkdir -p /var/lib/prometheus
sudo chown prometheus:prometheus /var/lib/prometheus

# Editar configuración (ver sección "Configurar prometheus.yml")
sudo nano /opt/prometheus/prometheus.yml

# Crear servicio
sudo tee /etc/systemd/system/prometheus.service > /dev/null <<EOF
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
ExecStart=/opt/prometheus/prometheus \
    --config.file=/opt/prometheus/prometheus.yml \
    --storage.tsdb.path=/var/lib/prometheus \
    --storage.tsdb.retention.time=30d

[Install]
WantedBy=multi-user.target
EOF

# Iniciar
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus

# Verificar
curl http://localhost:9090/api/v1/targets
```

#### Windows Server

```powershell
# Descargar desde https://github.com/prometheus/prometheus/releases
# Extraer a C:\prometheus\

# Editar C:\prometheus\prometheus.yml (ver sección "Configurar prometheus.yml")

# Instalar como servicio con NSSM
nssm install prometheus "C:\prometheus\prometheus.exe"
nssm set prometheus AppParameters "--config.file=C:\prometheus\prometheus.yml --storage.tsdb.path=C:\prometheus\data"
nssm set prometheus AppDirectory "C:\prometheus"

# Iniciar
nssm start prometheus

# Verificar
curl http://localhost:9090/api/v1/targets
```

---

### Paso 4: Instalar Grafana

#### Linux (Ubuntu/Debian)

```bash
# Agregar repositorio
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Instalar
sudo apt-get update
sudo apt-get install grafana

# Iniciar
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Verificar
curl http://localhost:3000
```

#### Linux (RHEL/CentOS)

```bash
# Agregar repositorio
sudo tee /etc/yum.repos.d/grafana.repo > /dev/null <<EOF
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
EOF

# Instalar
sudo yum install grafana

# Iniciar
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

#### Windows Server

```powershell
# Descargar instalador MSI desde https://grafana.com/grafana/download?platform=windows

# Ejecutar instalador
# Grafana se instala en C:\Program Files\GrafanaLabs\grafana

# El servicio se inicia automáticamente
# Verificar en http://localhost:3000
```

---

### Paso 5: Configurar Grafana

1. Abrir http://localhost:3000
2. Login inicial: `admin` / `admin` (te pedirá cambiarla)
3. Ir a **Connections** → **Data sources** → **Add data source**
4. Seleccionar **Prometheus**
5. URL: `http://localhost:9090`
6. Click **Save & Test**

---

## Configurar conexión a DB real

### 1. Crear usuario de monitoreo en PostgreSQL

Conecta a tu PostgreSQL y ejecuta:

```sql
-- Crear usuario de solo lectura para monitoreo
CREATE USER monitor_exporter WITH PASSWORD 'tu_password_seguro';

-- Permisos básicos
GRANT CONNECT ON DATABASE tu_database TO monitor_exporter;
GRANT USAGE ON SCHEMA public TO monitor_exporter;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_exporter;

-- Permisos para vistas de estadísticas (necesarios para postgres_exporter)
GRANT pg_monitor TO monitor_exporter;

-- Si tienes schema 'clients' para multi-tenant
GRANT USAGE ON SCHEMA clients TO monitor_exporter;
GRANT SELECT ON ALL TABLES IN SCHEMA clients TO monitor_exporter;
```

### 2. Editar queries.yml para tu schema

Edita `prometheus/queries.yml` y cambia `schemaname = 'clients'` por tu schema real:

```yaml
pg_client_tables:
  query: |
    SELECT
      schemaname,
      relname as client_name,
      ...
    FROM pg_stat_user_tables
    WHERE schemaname = 'TU_SCHEMA_AQUI'   # <-- Cambiar esto
```

Si no usas multi-tenant (una tabla por cliente), puedes eliminar el filtro `WHERE` para monitorear todas las tablas.

### 3. Configurar prometheus.yml

Edita `/opt/prometheus/prometheus.yml` (Linux) o `C:\prometheus\prometheus.yml` (Windows):

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Hardware - Linux usa puerto 9100, Windows usa 9182
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']   # Linux: 9100, Windows: 9182

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### 4. Configurar conexión del postgres_exporter

Edita la variable `DATA_SOURCE_NAME`:

```
DATA_SOURCE_NAME=postgresql://monitor_exporter:tu_password_seguro@IP_DEL_SERVIDOR:5432/nombre_database?sslmode=disable
```

Ejemplos:

```bash
# PostgreSQL local
DATA_SOURCE_NAME=postgresql://monitor_exporter:pass123@localhost:5432/production?sslmode=disable

# PostgreSQL remoto
DATA_SOURCE_NAME=postgresql://monitor_exporter:pass123@192.168.1.100:5432/production?sslmode=disable

# Con SSL
DATA_SOURCE_NAME=postgresql://monitor_exporter:pass123@db.empresa.com:5432/production?sslmode=require
```

### 5. Reiniciar servicios

```bash
# Linux
sudo systemctl restart postgres_exporter
sudo systemctl restart prometheus

# Windows
nssm restart postgres_exporter
nssm restart prometheus
```

### 6. Verificar conexión

```bash
# Ver métricas de PostgreSQL
curl http://localhost:9187/metrics | grep pg_

# Ver targets en Prometheus
curl http://localhost:9090/api/v1/targets
```

En Prometheus UI (http://localhost:9090/targets) todos los targets deben estar en estado **UP**.

---

## Estructura del proyecto

```
monitoring-stack/
├── docker-compose.yml          # Para desarrollo local
├── prometheus/
│   ├── prometheus.yml          # Config de Prometheus
│   └── queries.yml             # Custom queries para PostgreSQL
├── grafana/
│   └── provisioning/           # Auto-config de Grafana
├── postgres/
│   └── init/                   # Scripts de inicialización (solo Docker)
└── scripts/
    └── load_generator.py       # Generador de carga para testing
```

---

## Troubleshooting

### postgres_exporter no conecta

```bash
# Probar conexión manual
psql "postgresql://monitor_exporter:password@host:5432/database"

# Ver logs
journalctl -u postgres_exporter -f   # Linux
```

### Métricas de tablas no aparecen

1. Verificar que el schema en `queries.yml` sea correcto
2. Verificar que el usuario tenga permisos SELECT en las tablas
3. Revisar logs del postgres_exporter

### Windows: node_exporter no existe

Usar **windows_exporter** (puerto 9182):
- Descargar: https://github.com/prometheus-community/windows_exporter/releases
- Cambiar en prometheus.yml: `targets: ['localhost:9182']`

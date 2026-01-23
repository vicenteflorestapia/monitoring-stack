# Monitoring Stack

Prometheus + Grafana para monitoreo de hardware (CPU, RAM, Disco, GPU) y PostgreSQL.

## Contenido

- [Quick Start con Docker (desarrollo)](#quick-start-con-docker)
- [Instalación en Windows Server (producción)](#instalación-en-windows-server-producción)
- [Instalación en Linux (producción)](#instalación-en-linux-producción)
- [Configurar conexión a PostgreSQL](#configurar-conexión-a-postgresql)
- [Troubleshooting](#troubleshooting)

---

## Quick Start con Docker

Para desarrollo local:

```bash
# Copiar archivo de ejemplo y configurar credenciales
cp .env.example .env
# Editar .env con tus credenciales

# Levantar
docker-compose up -d

# Verificar
docker-compose ps
```

Acceder a:
- **Grafana:** http://localhost:3000
- **Prometheus:** http://localhost:9090

---

## Instalación en Windows Server (Producción)

### Requisitos previos

- Windows Server 2019/2022
- PowerShell como Administrador
- NSSM (descargar de https://nssm.cc/download)
- GPU NVIDIA con drivers instalados (opcional)

### Paso 1: Crear estructura de carpetas

```powershell
mkdir C:\monitoring
mkdir C:\monitoring\prometheus
mkdir C:\monitoring\postgres_exporter
mkdir C:\monitoring\windows_exporter
```

### Paso 2: Instalar Windows Exporter (CPU, RAM, Disco, Red)

```powershell
# Descargar última versión desde:
# https://github.com/prometheus-community/windows_exporter/releases

# Instalar MSI
msiexec /i windows_exporter-0.25.1-amd64.msi ENABLED_COLLECTORS="cpu,cs,logical_disk,memory,net,os,process,system" /qn

# Verificar (puerto 9182)
curl http://localhost:9182/metrics
```

### Paso 3: Instalar NVIDIA GPU Exporter (si tienes GPU)

```powershell
# Verificar que nvidia-smi funciona
nvidia-smi

# Descargar desde:
# https://github.com/utkuozdemir/nvidia_gpu_exporter/releases

# Extraer a C:\monitoring\nvidia_gpu_exporter\

# Instalar como servicio con NSSM
nssm install nvidia_gpu_exporter "C:\monitoring\nvidia_gpu_exporter\nvidia_gpu_exporter.exe"
nssm set nvidia_gpu_exporter AppDirectory "C:\monitoring\nvidia_gpu_exporter"
nssm start nvidia_gpu_exporter

# Verificar (puerto 9835)
curl http://localhost:9835/metrics
```

### Paso 4: Instalar Postgres Exporter

```powershell
# Descargar desde:
# https://github.com/prometheus-community/postgres_exporter/releases

# Extraer postgres_exporter.exe a C:\monitoring\postgres_exporter\

# Copiar queries.yml desde el repo a C:\monitoring\postgres_exporter\

# Instalar como servicio con NSSM
nssm install postgres_exporter "C:\monitoring\postgres_exporter\postgres_exporter.exe"
nssm set postgres_exporter AppParameters "--extend.query-path=C:\monitoring\postgres_exporter\queries.yml"
nssm set postgres_exporter AppEnvironmentExtra "DATA_SOURCE_NAME=postgresql://USUARIO:PASSWORD@localhost:5432/DATABASE?sslmode=disable"
nssm set postgres_exporter AppDirectory "C:\monitoring\postgres_exporter"

# Iniciar
nssm start postgres_exporter

# Verificar (puerto 9187)
curl http://localhost:9187/metrics
```

### Paso 5: Instalar Prometheus

```powershell
# Descargar desde:
# https://github.com/prometheus/prometheus/releases

# Extraer a C:\monitoring\prometheus\

# Copiar prometheus.yml desde el repo (o crear uno nuevo)
# Ver sección "Configurar prometheus.yml para Windows"

# Instalar como servicio con NSSM
nssm install prometheus "C:\monitoring\prometheus\prometheus.exe"
nssm set prometheus AppParameters "--config.file=C:\monitoring\prometheus\prometheus.yml --storage.tsdb.path=C:\monitoring\prometheus\data --storage.tsdb.retention.time=30d"
nssm set prometheus AppDirectory "C:\monitoring\prometheus"

# Iniciar
nssm start prometheus

# Verificar (puerto 9090)
curl http://localhost:9090/api/v1/targets
```

### Paso 6: Instalar Grafana

```powershell
# Descargar MSI desde:
# https://grafana.com/grafana/download?platform=windows

# Ejecutar instalador
# Se instala en C:\Program Files\GrafanaLabs\grafana
# El servicio inicia automáticamente

# Verificar (puerto 3000)
curl http://localhost:3000
```

## Configurar notificaciones por email (SMTP)

Para que Grafana pueda enviar alertas por correo electrónico:

### 1. Editar configuración de Grafana

**Windows:**
```powershell
notepad D:\monitoring\grafana\grafana\conf\grafana.ini
```

**Linux:**
```bash
sudo nano /etc/grafana/grafana.ini
```

### 2. Configurar sección [smtp]

Buscar la sección `[smtp]` y configurar según tu proveedor:

**Gmail / Google Workspace:**
```ini
[smtp]
enabled = true
host = smtp.gmail.com:587
user = servidor@flowhydro.cl
password = tu_app_password_aqui
from_address = servidor@flowhydro.cl
from_name = Grafana Alertas
skip_verify = false
```

**Office 365:**
```ini
[smtp]
enabled = true
host = smtp.office365.com:587
user = servidor@flowhydro.cl
password = tu_password_aqui
from_address = servidor@flowhydro.cl
from_name = Grafana Alertas
skip_verify = false
```

### 3. App Password para Gmail (si usa 2FA)

Si la cuenta de Gmail tiene verificación en 2 pasos:

1. Ir a https://myaccount.google.com/apppasswords
2. Login con la cuenta de correo
3. Crear App Password llamada "Grafana"
4. Usar esa contraseña de 16 caracteres en `grafana.ini`

### 4. Reiniciar Grafana

**Windows:**
```powershell
Restart-Service grafana
```

**Linux:**
```bash
sudo systemctl restart grafana-server
```

### 5. Probar configuración

En Grafana:
1. **Alerting** → **Contact points**
2. Click en tu contact point
3. Click **Test**
4. Click **Send test notification**

Deberías recibir un email de prueba.

---


### Paso 7: Configurar Grafana

1. Abrir http://localhost:3000
2. Login inicial: `admin` / `admin` (cambiar en primer login)
3. **Connections** → **Data sources** → **Add data source** → **Prometheus**
4. URL: `http://localhost:9090`
5. Click **Save & Test**

### Configurar prometheus.yml para Windows

Crear `C:\monitoring\prometheus\prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'windows'
    static_configs:
      - targets: ['localhost:9182']

  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['localhost:9835']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### Verificar todos los servicios

```powershell
# Ver servicios instalados
Get-Service prometheus, postgres_exporter, nvidia_gpu_exporter

# Ver en Prometheus UI
# http://localhost:9090/targets
# Todos deben estar en estado UP
```

---

## Instalación en Linux (Producción)

### Paso 1: Node Exporter (CPU, RAM, Disco, Red)

```bash
cd /tmp
curl -LO https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz
sudo mv node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter

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

sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
curl http://localhost:9100/metrics
```

### Paso 2: Postgres Exporter

```bash
cd /tmp
curl -LO https://github.com/prometheus-community/postgres_exporter/releases/download/v0.15.0/postgres_exporter-0.15.0.linux-amd64.tar.gz
tar xvfz postgres_exporter-0.15.0.linux-amd64.tar.gz
sudo mv postgres_exporter-0.15.0.linux-amd64/postgres_exporter /usr/local/bin/
sudo useradd -rs /bin/false postgres_exporter

sudo mkdir -p /etc/postgres_exporter
sudo tee /etc/postgres_exporter/postgres_exporter.env > /dev/null <<EOF
DATA_SOURCE_NAME=postgresql://USUARIO:PASSWORD@HOST:5432/DATABASE?sslmode=disable
EOF
sudo chmod 600 /etc/postgres_exporter/postgres_exporter.env

# Copiar queries.yml desde el repo
sudo cp prometheus/queries.yml /etc/postgres_exporter/queries.yml

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

sudo systemctl daemon-reload
sudo systemctl enable --now postgres_exporter
curl http://localhost:9187/metrics
```

### Paso 3: Prometheus

```bash
cd /tmp
curl -LO https://github.com/prometheus/prometheus/releases/download/v2.50.1/prometheus-2.50.1.linux-amd64.tar.gz
tar xvfz prometheus-2.50.1.linux-amd64.tar.gz
sudo mv prometheus-2.50.1.linux-amd64 /opt/prometheus
sudo useradd -rs /bin/false prometheus
sudo chown -R prometheus:prometheus /opt/prometheus
sudo mkdir -p /var/lib/prometheus
sudo chown prometheus:prometheus /var/lib/prometheus

# Editar /opt/prometheus/prometheus.yml

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

sudo systemctl daemon-reload
sudo systemctl enable --now prometheus
curl http://localhost:9090/api/v1/targets
```

### Paso 4: Grafana

```bash
# Ubuntu/Debian
sudo apt-get install -y software-properties-common
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana
sudo systemctl enable --now grafana-server
```

---

## Configurar conexión a PostgreSQL

### 1. Crear usuario de monitoreo

```sql
-- Conectar como superusuario
CREATE USER monitor_exporter WITH PASSWORD 'PASSWORD_SEGURO';

-- Permisos básicos
GRANT CONNECT ON DATABASE tu_database TO monitor_exporter;
GRANT USAGE ON SCHEMA public TO monitor_exporter;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_exporter;

-- Permisos para estadísticas del sistema
GRANT pg_monitor TO monitor_exporter;

-- Si usas schema específico (multi-tenant)
GRANT USAGE ON SCHEMA tu_schema TO monitor_exporter;
GRANT SELECT ON ALL TABLES IN SCHEMA tu_schema TO monitor_exporter;
```

### 2. Configurar DATA_SOURCE_NAME

```
DATA_SOURCE_NAME=postgresql://monitor_exporter:PASSWORD@localhost:5432/database?sslmode=disable
```

### 3. Editar queries.yml

Si usas multi-tenant (una tabla por cliente), edita `queries.yml` y cambia el schema:

```yaml
WHERE schemaname = 'tu_schema'
```

Si quieres monitorear todas las tablas, elimina la línea `WHERE`.

---

## Dashboards recomendados

Importar en Grafana (**Dashboards** → **Import**):

| ID | Nombre | Descripción |
|----|--------|-------------|
| 1860 | Node Exporter Full | CPU, RAM, Disco, Red (Linux) |
| 14694 | Windows Exporter | CPU, RAM, Disco, Red (Windows) |
| 9628 | PostgreSQL Database | Métricas de PostgreSQL |
| 14574 | NVIDIA GPU | Métricas de GPU |

---

## Estructura del proyecto

```
monitoring-stack/
├── docker-compose.yml          # Desarrollo local
├── .env.example                 # Ejemplo de variables de entorno
├── prometheus/
│   ├── prometheus.yml          # Config de Prometheus
│   └── queries.yml             # Custom queries PostgreSQL
├── grafana/
│   └── provisioning/           # Auto-config Grafana
├── postgres/
│   └── init/                   # Init scripts (solo Docker)
└── scripts/
    └── load_generator.py       # Generador de carga (testing)
```

---

## Troubleshooting

### Verificar servicios en Windows

```powershell
Get-Service prometheus, postgres_exporter, nvidia_gpu_exporter
nssm status prometheus
```

### Ver logs en Windows

```powershell
# Los logs están en el directorio de cada servicio
# O usar Event Viewer → Windows Logs → Application
```

### postgres_exporter no conecta

```powershell
# Probar conexión manual
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U monitor_exporter -d database -h localhost
```

### GPU no aparece en métricas

```powershell
# Verificar nvidia-smi
nvidia-smi

# Verificar exporter
curl http://localhost:9835/metrics | findstr "gpu"
```

### Reiniciar servicios

```powershell
nssm restart prometheus
nssm restart postgres_exporter
nssm restart nvidia_gpu_exporter
```

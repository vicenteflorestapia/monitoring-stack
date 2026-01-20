# Monitoring Stack - Prometheus + Grafana

Sistema de monitoreo de infraestructura (CPU, RAM, Disco, Red, GPU) y PostgreSQL usando Prometheus y Grafana.

## Contenido

- [Quick Start con Docker (desarrollo)](#quick-start-con-docker)
- [Instalación en Windows Server (producción)](#instalación-en-windows-server-producción)
- [Instalación en Linux (producción)](#instalación-en-linux-producción)
- [Configurar PostgreSQL](#configurar-postgresql)
- [Dashboards](#dashboards)
- [Troubleshooting](#troubleshooting)

---

## Quick Start con Docker

Para desarrollo local en Mac/Linux:

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
- NSSM (https://nssm.cc/download)
- GPU NVIDIA con drivers instalados (opcional)
- PostgreSQL instalado (si se va a monitorear DB)

### Estructura recomendada

Usar un disco separado (ejemplo: D:) para todos los componentes:

```
D:\monitoring\
├── prometheus\
├── postgres_exporter\
├── nvidia_gpu_exporter\
└── (instaladores temporales)
```

---

### Paso 1: Instalar NSSM

```powershell
# Descargar NSSM
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "D:\monitoring\nssm.zip"

# Extraer
Expand-Archive -Path "D:\monitoring\nssm.zip" -DestinationPath "D:\monitoring"

# Copiar al PATH del sistema
Copy-Item "D:\monitoring\nssm-2.24\win64\nssm.exe" "C:\Windows\System32\"

# Verificar
nssm version
```

---

### Paso 2: Instalar Windows Exporter (CPU, RAM, Disco, Red)

```powershell
# Descargar MSI desde:
# https://github.com/prometheus-community/windows_exporter/releases

# Instalar con collectors necesarios
msiexec /i windows_exporter-0.31.3-amd64.msi ENABLED_COLLECTORS="cpu,cs,logical_disk,memory,net,os,system,cpu_info" /qn

# Verificar servicio
Get-Service windows_exporter

# Verificar métricas (puerto 9182)
curl http://localhost:9182/metrics -UseBasicParsing
```

---

### Paso 3: Instalar NVIDIA GPU Exporter (opcional)

```powershell
# Verificar que nvidia-smi funciona
nvidia-smi

# Descargar desde:
# https://github.com/utkuozdemir/nvidia_gpu_exporter/releases
# Buscar archivo: nvidia_gpu_exporter-X.X.X-windows-amd64.zip

# Extraer en D:\monitoring\nvidia_gpu_exporter\
mkdir D:\monitoring\nvidia_gpu_exporter
Expand-Archive -Path "nvidia_gpu_exporter*.zip" -DestinationPath "D:\monitoring\nvidia_gpu_exporter"

# Registrar como servicio con NSSM
nssm install nvidia_gpu_exporter "D:\monitoring\nvidia_gpu_exporter\nvidia_gpu_exporter.exe"
nssm set nvidia_gpu_exporter AppDirectory "D:\monitoring\nvidia_gpu_exporter"
nssm start nvidia_gpu_exporter

# Verificar (puerto 9835)
curl http://localhost:9835/metrics -UseBasicParsing
```

---

### Paso 4: Instalar Postgres Exporter

```powershell
# Descargar desde:
# https://github.com/prometheus-community/postgres_exporter/releases

# Extraer en D:\monitoring\postgres_exporter\
mkdir D:\monitoring\postgres_exporter
Expand-Archive -Path "postgres_exporter*.zip" -DestinationPath "D:\monitoring\postgres_exporter"

# Copiar queries.yml desde el repo
Copy-Item "path\to\repo\prometheus\queries.yml" "D:\monitoring\postgres_exporter\queries.yml"

# Registrar como servicio con NSSM
nssm install postgres_exporter "D:\monitoring\postgres_exporter\postgres_exporter.exe"
nssm set postgres_exporter AppParameters "--extend.query-path=D:\monitoring\postgres_exporter\queries.yml"
nssm set postgres_exporter AppEnvironmentExtra "DATA_SOURCE_NAME=postgresql://USUARIO:PASSWORD@localhost:5432/DATABASE?sslmode=disable"
nssm set postgres_exporter AppDirectory "D:\monitoring\postgres_exporter"

# Iniciar
nssm start postgres_exporter

# Verificar (puerto 9187)
curl http://localhost:9187/metrics -UseBasicParsing
```

**Nota:** Reemplaza `USUARIO`, `PASSWORD`, y `DATABASE` con tus credenciales reales.

---

### Paso 5: Instalar Prometheus

```powershell
# Descargar desde:
# https://github.com/prometheus/prometheus/releases

# Extraer en D:\monitoring\prometheus\
mkdir D:\monitoring\prometheus
Expand-Archive -Path "prometheus*.zip" -DestinationPath "D:\monitoring\prometheus_temp"
Move-Item "D:\monitoring\prometheus_temp\prometheus-*\*" "D:\monitoring\prometheus\"
Remove-Item "D:\monitoring\prometheus_temp" -Recurse

# Copiar prometheus.yml desde el repo
Copy-Item "path\to\repo\prometheus\prometheus-windows.yml" "D:\monitoring\prometheus\prometheus.yml"

# Registrar como servicio con NSSM
nssm install prometheus "D:\monitoring\prometheus\prometheus.exe"
nssm set prometheus AppParameters "--config.file=D:\monitoring\prometheus\prometheus.yml --storage.tsdb.path=D:\monitoring\prometheus\data --storage.tsdb.retention.time=30d"
nssm set prometheus AppDirectory "D:\monitoring\prometheus"

# Iniciar
nssm start prometheus

# Verificar (puerto 9090)
curl http://localhost:9090/api/v1/targets -UseBasicParsing
```

---

### Paso 6: Instalar Grafana

```powershell
# Descargar MSI desde:
# https://grafana.com/grafana/download?platform=windows

# Ejecutar instalador
# Opcionalmente instalar en D:\monitoring\grafana

# El servicio se instala automáticamente

# Verificar servicio
Get-Service grafana

# Verificar (puerto 3000)
curl http://localhost:3000 -UseBasicParsing
```

---

### Paso 7: Configurar Grafana

1. Abrir http://localhost:3000
2. Login: `admin` / `admin` (cambiar en primer login)
3. **Connections** → **Data sources** → **Add data source**
4. Seleccionar **Prometheus**
5. URL: `http://localhost:9090`
6. Click **Save & Test**

---

### Verificar todos los servicios

```powershell
# Ver servicios corriendo
Get-Service windows_exporter, nvidia_gpu_exporter, postgres_exporter, prometheus, grafana

# Abrir Prometheus UI
Start-Process "http://localhost:9090/targets"

# Todos los targets deben estar en estado UP (verde)
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

# Copiar prometheus.yml desde el repo
sudo cp prometheus/prometheus.yml /opt/prometheus/prometheus.yml

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

## Configurar PostgreSQL

### 1. Crear usuario de monitoreo

Conectar a PostgreSQL como superusuario:

```sql
-- Crear usuario de solo lectura
CREATE USER monitor_exporter WITH PASSWORD 'PASSWORD_SEGURO';

-- Permisos básicos
GRANT CONNECT ON DATABASE tu_database TO monitor_exporter;

-- Permisos para estadísticas del sistema
GRANT pg_monitor TO monitor_exporter;

-- Permisos por schema (ajustar según necesidad)
GRANT USAGE ON SCHEMA public TO monitor_exporter;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_exporter;

-- Si tienes más schemas, repetir para cada uno:
-- GRANT USAGE ON SCHEMA mi_schema TO monitor_exporter;
-- GRANT SELECT ON ALL TABLES IN SCHEMA mi_schema TO monitor_exporter;
```

### 2. Configurar DATA_SOURCE_NAME

El connection string sigue este formato:

```
postgresql://monitor_exporter:PASSWORD@HOST:5432/DATABASE?sslmode=disable
```

**Ejemplos:**

- DB local: `postgresql://monitor_exporter:pass123@localhost:5432/production_db?sslmode=disable`
- DB remota: `postgresql://monitor_exporter:pass123@192.168.1.100:5432/mydb?sslmode=disable`

### 3. Personalizar queries.yml (opcional)

Si solo quieres monitorear schemas específicos, edita `queries.yml` y agrega filtros:

```yaml
WHERE schemaname IN ('public', 'mi_schema', 'otro_schema')
```

---

## Dashboards

### Dashboards recomendados de la comunidad

Importar en Grafana (**Dashboards** → **New** → **Import**):

| ID | Nombre | Descripción |
|----|--------|-------------|
| **14694** | Windows Exporter | CPU, RAM, Disco, Red (Windows) |
| **1860** | Node Exporter Full | CPU, RAM, Disco, Red (Linux) |
| **9628** | PostgreSQL Database | Métricas completas de PostgreSQL |
| **14574** | NVIDIA GPU | Métricas de GPU NVIDIA |

### Dashboard custom para Windows

Crear un dashboard personalizado con paneles básicos:

**CPU Usage:**
```promql
100 - (avg(irate(windows_cpu_time_total{mode="idle"}[5m])) * 100)
```

**Memory Usage:**
```promql
100 - ((windows_memory_available_bytes / windows_memory_physical_total_bytes) * 100)
```

**Disk Usage:**
```promql
100 - ((windows_logical_disk_free_bytes / windows_logical_disk_size_bytes) * 100)
```

**Network Traffic:**
```promql
rate(windows_net_bytes_total{nic=~".*Gigabit.*"}[5m])
```

**Tip:** Para mostrar solo el nombre del volumen en la leyenda de Disk Usage, usar en **Standard options → Display name**: `${__field.labels.volume}`

---

## Troubleshooting

### Servicios en Windows

```powershell
# Ver estado de servicios
Get-Service windows_exporter, nvidia_gpu_exporter, postgres_exporter, prometheus, grafana

# Ver status NSSM
nssm status prometheus
nssm status postgres_exporter
nssm status nvidia_gpu_exporter

# Reiniciar un servicio
nssm restart prometheus
```

### Problemas comunes

#### Dashboard de Windows muestra N/A en CPU, Memory, Disk

**Causa:** Faltan collectors en Windows Exporter

**Solución:**
1. Desinstalar Windows Exporter actual
2. Reinstalar con collectors completos:
   ```powershell
   msiexec /i windows_exporter-0.31.3-amd64.msi ENABLED_COLLECTORS="cpu,cs,logical_disk,memory,net,os,system,cpu_info" /qn
   ```

#### Postgres Exporter no conecta a la DB

**Verificar conexión manual:**
```powershell
& "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U monitor_exporter -d database -h localhost
```

**Revisar DATA_SOURCE_NAME:**
```powershell
nssm get postgres_exporter AppEnvironmentExtra
```

#### GPU no aparece en métricas

**Verificar driver NVIDIA:**
```powershell
nvidia-smi
```

**Verificar exporter:**
```powershell
curl http://localhost:9835/metrics -UseBasicParsing | Select-String "gpu"
```

#### Prometheus no muestra targets en UP

**Verificar prometheus.yml:**
```powershell
notepad D:\monitoring\prometheus\prometheus.yml
```

Debe tener los 4 jobs: prometheus, windows, nvidia-gpu, postgres

**Reiniciar Prometheus:**
```powershell
nssm restart prometheus
```

#### Dashboards importados no muestran datos

**Verificar en Prometheus UI:**
1. Abrir http://localhost:9090
2. Status → Targets
3. Todos deben estar en UP (verde)

**Probar query en Prometheus:**
- Graph → Ejecutar: `windows_cpu_time_total`
- Debe devolver datos

Si no devuelve datos, el problema está en la recolección de métricas, no en Grafana.

---

## Estructura del proyecto

```
monitoring-stack/
├── docker-compose.yml          # Desarrollo local
├── .env.example                # Ejemplo de variables de entorno
├── .gitignore
├── prometheus/
│   ├── prometheus-windows.yml  # Config para Windows Server
│   ├── prometheus.yml          # Config para Linux/Docker
│   └── queries.yml             # Custom queries PostgreSQL
├── grafana/
│   └── provisioning/           # Auto-config Grafana (Docker)
├── postgres/
│   └── init/                   # Init scripts (solo Docker)
└── README.md
```

---

## Puertos utilizados

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Grafana | 3000 | UI de visualización |
| Prometheus | 9090 | UI y API de Prometheus |
| Windows Exporter | 9182 | Métricas de Windows |
| Postgres Exporter | 9187 | Métricas de PostgreSQL |
| NVIDIA GPU Exporter | 9835 | Métricas de GPU |
| Node Exporter (Linux) | 9100 | Métricas de Linux |

---

## Recursos adicionales

- [Documentación oficial de Prometheus](https://prometheus.io/docs/)
- [Documentación oficial de Grafana](https://grafana.com/docs/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Windows Exporter Collectors](https://github.com/prometheus-community/windows_exporter#collectors)

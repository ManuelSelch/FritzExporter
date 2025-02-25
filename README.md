## Overview
- This script (fritzbox_scrapper.py) fetches all logs from FritzBox and sends all new logs to Loki
- Therefore it needs to store the last log date (data/last_log.json) to filter new logs

## Setup
- copy .env.example to .env and setup all parameters.
- Create a new FritzBox account that has access rights to the FritzBox settings
- install Grafana (dashboard) and Loki (log storage)

```env
FRITZ_HOST = "http://fritz.box"
FRITZ_USER = "<USER>"
FRITZ_PASS = "<PASS>"

LOKI_HOST = "https://<HOST>"
LOG_FILE = ".data/last_log.json"
```

## Prometheus & Grafana & Loki 
This is a simple docker-compose config to create a grafa and loki container.
Also i use prometheus and a FritzBox exporter to log some FritzBox statistics.

```bash
volumes:
  prometheus_data: {}
  grafana_data: {}

networks:
  proxynet:
    name: proxynet
    external: true

services:
  prometheus:
    image:
      prom/prometheus
    container_name: prometheus
    volumes: 
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - proxynet
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - proxynet
    env_file:
      - .env.grafana
    restart: unless-stopped

  pushgateway:
    image: prom/pushgateway
    container_name: pushgateway
    networks:
      - proxynet
    restart: unless-stopped

  fritz-exporter:
    image: pdreker/fritz_exporter:2
    container_name: fritz-exporter
    networks:
      - proxynet
    env_file:
      - .env.fritz
    restart: unless-stopped
  
  loki:
    image: grafana/loki:latest
    container_name: loki
    networks:
      - proxynet
    restart: unless-stopped
```

This is the corresbonding prometheus config:
```bash
global:
  scrape_interval: 15s 
  evaluation_interval: 15s

alerting:
scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
 
  - job_name: "pushgateway"
    honor_labels: true
    static_configs:
      - targets: ["pushgateway:9091"]

  - job_name: "fritz-exporter"
    static_configs:
      - targets: ["fritz-exporter:9787"]
```

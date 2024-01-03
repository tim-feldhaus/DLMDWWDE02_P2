# DLMDWWDE02_Aufgabenstellung_2

## Quellen der verwendeten Daten:

### NYC Taxifahrten (.\generator\data)
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

### NYC Taxi Zonen (.\pyflink\data\taxi_zones):
https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc

## Vorgehen und Informationen

Die Implementierung des Konzepts aus der vorherigen Konzeptionsphase wird schrittweise durchgeführt, beginnend beim Data Source-Layer bis hin zum Data Visualization-Layer entlang des Flows aus der zuvor dargestellten Abbildung. In jedem Schritt wird der nachfolgende Layer betrachtet, um die erforderlichen Informationen zu identifizieren.

### Data Source: 
Die Datensätze der NYC Taxifahrten werden von " https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page" heruntergeladen und im Verzeichnis ".\generator\data" abgelegt.
Es wird ein Docker Container mit Python (python:3.8-slim) verwendet und weitere benötigte Abhängigkeiten installiert. 
Außerdem wird ein Python-Skript "write_tripdata.py" erstellt, dass die Parquet-Datensätze in ein JSON konvertiert und nach Kafka sendet. Die Daten werden in den Container hinein gemountet und das Skript ausgeführt.

### Data Ingestion: 
Es wird ein Docker Container mit Apache Kafka (wurstmeister/kafka:2.13-2.8.1) verwendet. Der Container wird durch Umgebungsvariablen konfiguriert. 
Kafka hängt von Zookeeper ab, hierfür wird der Docker Container (wurstmeister/zookeeper:3.4.6) verwendet.

### Data Processing: 
Für die Echtzeitverarbeitung mit Apache Flink wird der Docker Container "apache/flink:1.17.1-scala_2.12-java11" verwendet. Darüber hinaus werden weitere Abhängigkeiten installiert, die für die Ausführung des Python-Skript (PyFlink) benötigt werden.
Das Docker Image wird zum einen als Jobmanager-Container und zum anderen als Taskmanager-Container verwendet.
Elasticsearch benötigt einen "geo_point", damit die Datensätzen anschließend visualisiert werden können. Hierfür werden die Shape-Daten von den NYC Taxi Zonen ( https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc) heruntergeladen und im Verzeichnis ".\pyflink\data" abgelegt. Die Daten werden in den Container hinein gemountet.
Das Skript berechnet von jeder Taxi Zone den Mittelpunkt (centroid) und ergänzt diese Informationen zum bestehenden Datensatz. Außerdem werden die Daten auf die nur noch relevanten Daten (passenger_count, tpep_dropoff_datetime und berechneter centroid) reduziert und nach Elasticsearch gesendet.

### Data Storage:
Es wird ein Docker Container mit Elasticsearch (elasticsearch:7.17.13) verwendet. Der Container wird durch Umgebungsvariablen konfiguriert. 

### Data Visualization: 
Es wird ein Docker Container mit Kibana (kibana:7.17.3) verwendet. Um Kibana zu konfigurieren, wird ein weiter Docker Container (alpine:3.18) verwendet, der durch ein Bash-Skript eine Konfigurationsdatei (./kibana/export.ndjson) nach Kibana lädt. Dort enthalten ist ein Dashboard einer Map, der benötigte Index-Pattern und die Aggregationslayer auf der Map, welche die Anzahl der ausgestiegenen Passagiere pro Stadtbezirk aggregiert und visualisiert.
\
\

Im Anschluss wird ein docker-compose.yml erstellt, welches die vorher genannten Docker Container erstellt bzw. konfiguriert. Die gesamte Umgebung kann per "docker-compose up" hochgefahren werden. Damit Apache Flink den Daten verarbeitet, muss das Skript "exec_job.bat" ausgeführt werden, wodurch ein Apache Flink-Job mit dem Python-Skript erstellt wird.
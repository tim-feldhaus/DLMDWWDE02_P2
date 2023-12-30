FROM apache/flink:1.17.1-scala_2.12-java11
ARG FLINK_VERSION=1.17.1
ARG ELASTICSEARCH_VERSION=3.0.1-1.17
  
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-json/${FLINK_VERSION}/flink-json-${FLINK_VERSION}.jar; \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/${FLINK_VERSION}/flink-sql-connector-kafka-${FLINK_VERSION}.jar; \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-elasticsearch7/${ELASTICSEARCH_VERSION}/flink-sql-connector-elasticsearch7-${ELASTICSEARCH_VERSION}.jar;

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    python -m pip install --upgrade pip && \
    pip install apache-flink==${FLINK_VERSION}; \
    pip install pyshp; \
    pip install pandas; \
    pip install geopandas;

ADD process_tripdata.py /

WORKDIR /opt/flink
import os
from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.table import StreamTableEnvironment, DataTypes, EnvironmentSettings
from pyflink.common.typeinfo import Types
from pyflink.table.descriptors import Schema
from pyflink.table.expressions import call, col
from pyflink.table.udf import udf
import pandas as pd
import geopandas as gpd
from datetime import datetime
import requests
import json

DATA_PATH = os.getenv('DATA_PATH')

shapefile_df = gpd.read_file(
    DATA_PATH + '/' + 'taxi_zones' + '/' + 'taxi_zones.shp')
shapefile_df["centroid"] = shapefile_df["geometry"].centroid.to_crs(epsg=4326)


def create_mapping():
    index_name = 'tripdata'
    mapping = {
        "mappings": {
            "properties": {
                "location": {
                    "type": "geo_point"
                },
                "cnt": {
                    "type": "double"
                },
                "dropoff_time": {
                    "type": "date"
                }
            }
        }
    }

    es_url = 'http://elasticsearch:9200/' + index_name
    response = requests.put(es_url, json=mapping)

    if response.status_code == 200:
        print(f"Mapping for index '{index_name}' created successfully.")
    else:
        print(
            f"Failed to create mapping for index '{index_name}'. Status code: {response.status_code}, Response: {response.text}")


@udf(input_types=[DataTypes.INT()], result_type=DataTypes.STRING())
def location_id_to_centroid(location_id):
    centroid = shapefile_df.loc[shapefile_df['LocationID']
                                == location_id, 'centroid']
    if (centroid.empty):
        return "empty"
    return centroid.iloc[0].wkt


def process_tripdata():
    env = StreamExecutionEnvironment.get_execution_environment()
    t_env = StreamTableEnvironment.create(stream_execution_environment=env)

    create_kafka_source_ddl = """
            CREATE TABLE kafka_source(
                VendorID INT,
                tpep_pickup_datetime VARCHAR,
                tpep_dropoff_datetime VARCHAR,
                passenger_count DOUBLE,
                trip_distance DOUBLE,
                RatecodeID DOUBLE,
                store_and_fwd_flag VARCHAR,
                PULocationID INT,
                DOLocationID INT,
                payment_type INT,
                fare_amount DOUBLE,
                extra DOUBLE,
                mta_tax DOUBLE,
                tip_amount DOUBLE,
                tolls_amount DOUBLE,
                improvement_surcharge DOUBLE,
                total_amount DOUBLE,
                congestion_surcharge DOUBLE,
                airport_fee DOUBLE
            ) WITH (
                'connector' = 'kafka',
                'topic' = 'tripdata',
                'properties.bootstrap.servers' = 'kafka:9092',
                'properties.group.id' = '1',
                'scan.startup.mode' = 'latest-offset',
                'format' = 'json'
            )
            """

    create_es_sink_ddl = """
            CREATE TABLE es_sink(
                location VARCHAR,
                cnt DOUBLE,
                dropoff_time VARCHAR
            ) with (
                'connector' = 'elasticsearch-7',
                'hosts' = 'http://elasticsearch:9200',
                'index' = 'tripdata',
                'document-id.key-delimiter' = '$',
                'sink.bulk-flush.max-size' = '42mb',
                'sink.bulk-flush.max-actions' = '32',
                'sink.bulk-flush.interval' = '1000',
                'sink.bulk-flush.backoff.delay' = '1000',
                'format' = 'json'
            )
    """

    t_env.execute_sql(create_kafka_source_ddl)
    t_env.execute_sql(create_es_sink_ddl)

    t_env.register_function('location_id_to_centroid', location_id_to_centroid)
    create_mapping()
    t_env.from_path("kafka_source") \
        .select(call('location_id_to_centroid', col('DOLocationID')).alias('location'), col('passenger_count').alias('cnt'), col('tpep_dropoff_datetime').alias('dropoff_time')) \
        .filter(col('location') != "empty") \
        .execute_insert("es_sink")


if __name__ == '__main__':
    process_tripdata()

import os
import glob
import sys
import datetime
import logging
import json
import pandas as pd
from decimal import Decimal
from time import sleep
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka import errors

FIRST_VALID_DATETIME_ENTRY = '2023-01-01 00:00:47'
SIMULATION_SPEED_FACTOR = os.getenv('SIMULATION_SPEED_FACTOR', 1)

DATA_PATH = os.getenv('DATA_PATH')
KAFKA_SERVER = "kafka:9092"
KAFKA_TOPIC = "tripdata"

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO)

logger = logging.getLogger()


class SimulateDelayException(Exception):
    pass


def find_and_sort_parquet_files(directory):
    parquet_files = glob.glob(os.path.join(directory, '*.parquet'))
    return sorted(parquet_files)


def calculate_percentage(subtotal, total):
    if total == 0:
        return 0.0
    return (Decimal(subtotal)/Decimal(total)*Decimal(100)).quantize(Decimal("0.00"))


def simulate_delay(timestamp):
    base_timestamp = datetime.strptime(
        FIRST_VALID_DATETIME_ENTRY, '%Y-%m-%d %H:%M:%S')
    time_difference = timestamp - base_timestamp
    sec = time_difference.total_seconds()
    if (sec < 0):
        raise SimulateDelayException('invalid_entry')
    speed_factor = int(SIMULATION_SPEED_FACTOR)
    if (speed_factor <= 0):
        speed_factor = 1
    sleepForSeconds = sec / speed_factor
    sleep(sleepForSeconds)


def manipulate_timestamp(df):
    dropoff_datetime = datetime.now()
    pickup_delta = df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']
    pickup_datetime = dropoff_datetime - pickup_delta
    df['tpep_dropoff_datetime'] = dropoff_datetime
    df['tpep_pickup_datetime'] = pickup_datetime
    return df


def write_tripdata(producer):
    parquet_files = find_and_sort_parquet_files(DATA_PATH)
    all_rows = 0
    for file in parquet_files:
        df = pd.read_parquet(file)
        all_rows += len(df)

    all_processed_rows = 0
    for file_index, file in enumerate(parquet_files):
        df = pd.read_parquet(file)
        sorted_df = df.sort_values(
            by=['tpep_dropoff_datetime'], ascending=True)
        cur_processed_rows = 0
        for row_index, row in sorted_df.iterrows():
            cur_processed_rows += 1
            all_processed_rows += 1
            output = "Current progress (file: {}/{}): {}/{} ({}%). Overall progress: {}/{} ({}%)" \
                .format(
                    file_index+1,
                    len(parquet_files),
                    cur_processed_rows,
                    len(df),
                    calculate_percentage(cur_processed_rows, len(df)),
                    all_processed_rows,
                    all_rows,
                    calculate_percentage(all_processed_rows, all_rows)
                )
            if (all_processed_rows == 1):
                logger.info(output)
            if (all_processed_rows % 10000 == 0):
                logger.info(output)
            try:
                simulate_delay(row['tpep_dropoff_datetime'])
            except SimulateDelayException as e:
                continue
            manipulated_row = manipulate_timestamp(row)
            json_data = manipulated_row.to_json(date_format="iso")
            producer.send(KAFKA_TOPIC, value=json_data)


def create_producer():
    logger.info("Connecting to Kafka brokers")
    for i in range(0, 6):
        try:
            producer = KafkaProducer(bootstrap_servers=[KAFKA_SERVER],
                                     value_serializer=lambda x: bytes(
                                         x.encode('utf-8'))
                                     )
            logger.info("Connected to Kafka")
            return producer
        except errors.NoBrokersAvailable:
            logger.info("Waiting for brokers to become available")
            sleep(10)
    raise RuntimeError("Failed to connect to brokers within 60 seconds")


if __name__ == '__main__':
    try:
        producer = create_producer()
        write_tripdata(producer)
    except Exception as e:
        logger.error(e)

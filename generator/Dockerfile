FROM python:3.8-slim

RUN python -m pip install --upgrade pip; \
    pip install kafka-python; \
    pip install numpy; \
    pip install pandas; \
    pip install pyarrow; 

ADD write_tripdata.py /

CMD ["python", "-u", "./write_tripdata.py"]
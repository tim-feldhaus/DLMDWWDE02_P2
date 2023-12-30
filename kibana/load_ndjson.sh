until curl -s kibana:5601/login -o /dev/null; do
    echo Waiting for Kibana...
    sleep 10
done

curl -X POST kibana:5601/api/saved_objects/_import -H "kbn-xsrf: true" --form file=@/tmp/load/export.ndjson

echo 'all loaded up'
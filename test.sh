 curl http://localhost:8888/api/dirs
 curl http://localhost:8888/api/dirs \
    -H "Content-Type: application/json" \
    -d '{
        "dirs": [
          {"path":"/home/"},
          {"path":"/Users/sauravahmed/"}
        ]
    }'


 curl http://localhost:8888/api/interval
 curl http://localhost:8888/api/interval \
    -H "Content-Type: application/json" \
    -d '{
      "interval": 389
    }'


 curl http://localhost:8888/api/dryrun
 curl http://localhost:8888/api/dryrun \
    -H "Content-Type: application/json" \
    -d '{
      "dryrun": true
    }'



 curl http://localhost:8888/api/data

#
# DOCKER — ELASTICSEARCH — KIBANA
#
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.8.1
docker pull docker.elastic.co/kibana/kibana:8.8.1

docker network create elastic # create docker network

docker run --name es01 --net elastic -p 9200:9200 -it docker.elastic.co/elasticsearch/elasticsearch:8.8.1
docker run --name kibana --net elastic -p 5601:5601 docker.elastic.co/kibana/kibana:8.8.1 # run in terminal, not desktop (cannot pass arguments)

docker cp es01:/usr/share/elasticsearch/config/certs/http_ca.crt .
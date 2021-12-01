docker rm -f crawler
docker image rm crawler:1

docker build --tag crawler:1 .
docker run --name crawler -p 8094:8094 -d crawler:1 


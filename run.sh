sudo docker rm -f dagsplat
sudo docker run \
    -d \
    --name dagsplat \
    -e DAGSTER_HOME=/dagster/.dagster_home \
    --restart always \
    -p 3000:3000 \
    -v $(pwd)/data:/dagster/data \
    -v $(pwd)/.dagster_home_docker:/dagster/.dagster_home \
    dagsplat:0.0.1

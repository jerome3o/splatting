sudo docker rm -f dagsplat
sudo docker run --name dagsplat -v $(pwd)/data:/dagster/data -d -p 3000:3000 dagsplat:0.0.1

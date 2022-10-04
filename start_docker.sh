docker build -t dogecoin-mapper .
sudo systemctl start podman
sudo docker-compose up --build --force-recreate
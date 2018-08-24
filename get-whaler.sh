curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu
apt-get install -y docker-compose
git clone https://github.com/oncyberblog/whaler.git
systemctl enable docker
apt-get update && apt-get upgrade
reboot now

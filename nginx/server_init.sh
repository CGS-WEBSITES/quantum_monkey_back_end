printf "====> Atualizando servidor\n"

sudo apt-get update

sudo apt-get upgrade -y

printf "====> Configurando NGINX\n"

curl -O https://nginx.org/download/nginx-1.23.4.tar.gz

tar -zxvf nginx-1.23.4.tar.gz nginx-1.23.4

cd nginx-1.23.4/

sudo apt-get install build-essential libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev -y

./configure --sbin-path=/usr/bin/nginx --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --with-pcre --pid-path=/var/run/nginx.pid --with-http_ssl_module

make

sudo make install

cd ..

sudo mv -f nginx.service /lib/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable nginx

sudo systemctl start nginx

printf "\n\n\Servidor pronto!\n\n"

CREATE DATABASE  IF NOT EXISTS `drunagor_teste`;

CREATE USER IF NOT EXISTS 'drunagor_dev'@'%' IDENTIFIED BY '12345';

GRANT ALL PRIVILEGES ON drunagor_teste.* TO 'drunagor_dev'@'%';


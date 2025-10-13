CREATE DATABASE  IF NOT EXISTS `qmonkey_test`;

CREATE USER IF NOT EXISTS 'qmonkey_dev'@'%' IDENTIFIED BY '12345';

GRANT ALL PRIVILEGES ON qmonkey_teste.* TO 'qmonkey_dev'@'%';


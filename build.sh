#!/bin/bash

VALID_ARGS=$(getopt -o p,t,a,l,h --long production,test,all,local,help -- "$@")
if [[ $? -ne 0 ]]; then
    exit 1
fi

eval set -- "$VALID_ARGS"
while [ : ]; do
    case "$1" in
    -p | --production)
        echo " -----> CGS-DRUNAGOR DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Production Container"
        echo

        docker build ./api_mysql/ -t api_mysql:prod

        #############################################

        echo "  ---> Building NGINX Container"
        echo

        docker build ./nginx/ -t nginx_px

        shift
        ;;
    -t | --test)

        echo " -----> CGS-DRUNAGOR DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Test Container"
        echo

        docker build ./api_mysql/ -t api_mysql:test

        #############################################

        echo "  ---> Building NGINX Container"
        echo

        docker build ./nginx/ -t nginx_px

        shift
        ;;
    -a | --all)

        echo " -----> CGS-DRUNAGOR DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Production Container"
        echo

        docker build ./api_mysql/ -t api_mysql:prod

        #############################################

        echo "  ---> Building Flask MySQL Test Container"
        echo

        docker build ./api_mysql/ -t api_mysql:test

        #############################################

        echo "  ---> Building NGINX Container"
        echo

        docker build ./nginx/ -t nginx_px

        shift
        ;;

    -l | --local)

        echo " -----> CGS-DRUNAGOR DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Local Container"
        echo

        docker build ./api_mysql/ -t api_mysql:local

        #############################################

        echo "  ---> Building MySQL Local Container"
        echo

        docker build ./mysql/ -t mysql_db:local

        #############################################

        echo "  ---> Building NGINX Container"
        echo

        docker build ./nginx/ -t nginx_px

        shift
        ;;
    -h | --help)
        echo " -----> Helper <----- "

        echo "-p | --production      build application for production"
        echo "-t | --test            build application for test"
        echo "-a | --all             build application for both"
        echo "-l | --local           build application for local containers"

        shift
        ;;
    --)
        shift
        break
        ;;
    esac
done

#!/bin/bash

VALID_ARGS=$(getopt -o p,t,a,l,h --long production,test,all,local,help -- "$@")
if [[ $? -ne 0 ]]; then
    exit 1
fi

eval set -- "$VALID_ARGS"
while [ : ]; do
    case "$1" in
    -p | --production)
        echo " -----> CGS-QUANTUM MONKEY DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Production Container"
        echo

        docker --debug build ./api_mysql/ -t api_qmonkey:prod 

        shift
        ;;
    -t | --test)

        echo " -----> CGS-QUANTUM MONKEY DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Test Container"
        echo

        docker --debug build ./api_mysql/ -t api_qmonkey:test

        shift
        ;;
    -a | --all)

        echo " -----> CGS-QUANTUM MONKEY DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Production Container"
        echo

        docker build ./api_mysql/ -t api_qmonkey:prod


        shift
        ;;

    -l | --local)

        echo " -----> CGS-QUANTUM MONKEY DOCKER <----- "
        echo

        echo "  ---> Building Flask MySQL Local Container"
        echo

        docker build ./api_mysql/ -t api_qmonkey:local

        #############################################

        echo "  ---> Building MySQL Local Container"
        echo

        docker build ./mysql/ -t mysql_db:local

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

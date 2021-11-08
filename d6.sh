#!/bin/bash

DOCKER=/usr/bin/docker
COMPOSE_FILE="./docker/compose/docker-compose.yml"
# IMAGES=("atmoz/sftp" "stilliard/pure-ftpd")
IMAGES=("ftp_secure_sftp" "ftp_secure_ftp_tls")
SHELL=/bin/bash # Sometimes only /bin/sh is available
ACTION=$1
IMAGE_NO=$2

usage() {
    echo
    echo "Usage:"
    echo "      ./d6.sh <action> [image no]"
    echo
    echo "The [image no] is used only with TTY. Specify 0, 1, etc."
}

build() {
    # Remove any existing cruft of the ED25519 key fingerprint
    ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[localhost]:2222" >/dev/null 2>&1

    docker-compose -p ftp_secure -f $COMPOSE_FILE build
    docker-compose -p ftp_secure -f $COMPOSE_FILE up --detach
}

# Running containers only
get_running_container_id() {
    FILTER="ancestor=$1"
    ID="$DOCKER ps --no-trunc -qf '$FILTER' -f 'status=running'"
    ID=$(eval "$ID")
    if [[ "$ID" != "" ]]; then
        echo "$ID"
    else
        false
    fi
}

# Regardless of running or not
get_container_id() {
    FILTER="ancestor=$1"
    ID="$DOCKER ps --no-trunc -qf '$FILTER' -a"
    ID=$(eval "$ID")
    if [[ "$ID" != "" ]]; then
        echo "$ID"
    else
        false
    fi
}

running_container_action() {
    case "$ACTION" in
    tty | shell)
        # Can only tty to a specified image number.
        if [[ "$IMAGE_NO" == "" ]]; then
            usage
            exit 1
        fi

        if [[ "$IMAGE_NO" == "$2" ]]; then
            eval "$DOCKER exec -it $1 $SHELL"
            exit 0
        fi
        ;;
    stop | rm | rmi | destory | rebuild)
        # Anything running must be stopped
        if [[ "$IMAGE_NO" == "" || "$IMAGE_NO" == "$2" ]]; then
            eval "$DOCKER stop $1"
        fi
        ;;
    build)
        # If even one of the images has a running container, get out quick
        echo
        echo "Already running: [$1]"
        echo "      for image: [${IMAGES[$2]}]."
        echo
        echo "Stop all containers before doing a build."
        echo
        exit 1
        ;;
    esac
}

existing_container_action() {
    # Assume anything getting to this point has been stopped
    case "$ACTION" in
    rm)
        if [[ "$IMAGE_NO" == "" || "$IMAGE_NO" == "$2" ]]; then
            eval "$DOCKER rm $1"
        fi
        ;;

    rmi | destroy)
        if [[ "$IMAGE_NO" == "" || "$IMAGE_NO" == "$2" ]]; then
            set -xe
            # Remove the container
            eval "$DOCKER rm $1"
            # Remove the image
            eval "$DOCKER rmi ${IMAGES[$i]}"
        fi
        ;;

    build | rebuild)
        if [[ "$IMAGE_NO" == "" || "$IMAGE_NO" == "$2" ]]; then
            eval "$DOCKER rm $1"
        fi
        ACTION=build # reassigns
        ;;
    esac
}

# ----------- Start code --------------------------------------------------

# Containerless and non-docker commands
case "$ACTION" in
'')
    usage
    exit 1
    ;;
list)
    echo
    echo "-- IMAGES ---------"
    $DOCKER image ls
    echo "-- CONTAINERS -----"
    # Same as docker ps
    $DOCKER container ls
    exit 0
    ;;
ps)
    $DOCKER ps -a
    exit 0
    ;;
ftp)
    ftp -p -d -v localhost 21
    exit 0
    ;;
sftp)
    sftp -P 2222 anthony@localhost
    exit 0
    ;;
netstat)
    # e is extended -> gives pid
    # a gives all (LISTEN + ESTABLISHED)
    # l gives LISTEN
    # p gives the pids/program names
    # u give UDP
    echo "-- PORT 2222 -------"
    sudo netstat -plnt | grep :2222
    echo "-- PORT 21 -------"
    sudo netstat -plnt | grep :21
    exit 0
    ;;
esac

# Find running containers
running_containers=()
image_nos=()
for ((i = 0; i < ${#IMAGES[@]}; i++)); do
    container=$(get_running_container_id ${IMAGES[$i]})
    if [[ "$container" != "" ]]; then
        running_containers+=("$container")
        image_nos+=("$i")
    fi
done

# Perform actions on any running containers
for ((i = 0; i < ${#running_containers[@]}; i++)); do
    running_container_action "${running_containers[$i]}" "${image_nos[$i]}"
done

# Find existing containers, stopped or otherwise
containers=()
image_nos=()
for ((i = 0; i < ${#IMAGES[@]}; i++)); do
    container=$(get_container_id ${IMAGES[$i]})
    if [[ "$container" != "" ]]; then
        containers+=("$container")
        image_nos+=("$i")
    fi
done

# Perform actions on any existing container, stopped or otherwise
for ((i = 0; i < ${#containers[@]}; i++)); do
    existing_container_action "${containers[$i]}" "${image_nos[$i]}"
done

# Will drop through to here with a build
if [[ "$ACTION" == "build" ]]; then
    if build; then
        echo
        echo "-- CONTAINERS -----"
        $DOCKER container ls
    fi
fi

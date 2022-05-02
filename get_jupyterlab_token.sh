#!/bin/bash
# GET JUPYTERLAB TOKEN.sh
#   by Lut99
#
# Created:
#   28 Apr 2022, 13:41:41
# Last edited:
#   28 Apr 2022, 13:49:31
# Auto updated?
#   Yes
#
# Description:
#   Simple script that indefinitely tries to read the jupyterlab token /
#   launch URL from the 'brane-ide' docker container.
#


# Loop to find it, waiting half a second to give the lab time to boot
url=""
while [[ -z "$url" ]]; do
    # Wait to not make it a busy loop
    sleep 0.5

    # Get the logs of the container
    logs=$(docker logs brane-ide 2>&1)
    if [[ "$?" -ne 0 ]]; then
        echo "Could not get docker logs:"
        echo " > $logs"
        exit "$?"
    fi

    # Parse the container input to fetch the token
    url="$(echo "$logs" | grep "lab?token=" | tail -1 | awk '{$1=$1};1')"
    
    # If there was a token, $url is now non-empty
done

# Print the URL
echo "$url"

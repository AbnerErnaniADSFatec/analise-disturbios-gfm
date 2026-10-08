#!/bin/bash

# ==================================================
# Read and set inputs

read -p "Email: " EMAIL_RAW
EMAIL=$(echo "$EMAIL_RAW" | sed 's/@/%40/')

read -s -p "App password: " PASS; echo
PASSWORD=$(rclone obscure "$PASS")

echo "Escolha o servidor Nextcloud:"
echo "1) data.inpe.br"
echo "2) geolab.inpe.br"
read -p "Digite 1 ou 2: " CHOICE
if [ "$CHOICE" = "1" ]; then
  NEXTCLOUD_URL="https://data.inpe.br/big/nextcloud"
elif [ "$CHOICE" = "2" ]; then
  NEXTCLOUD_URL="https://geolab.inpe.br/big/nextcloud"
else
  echo "Opção inválida. Abortando."
  exit 1
fi

# ==================================================
# Write config file

CONF_FILEPATH=$HOME/.config/rclone/rclone.conf

printf "[nextcloud]\n\
type = webdav\n\
url = ${NEXTCLOUD_URL}/remote.php/dav/files/%s\n\
vendor = nextcloud\n\
user = %s\n\
pass = %s\n" "$EMAIL" "$EMAIL_RAW" "$PASSWORD" >> ${CONF_FILEPATH}

echo "Finalizado! O arquivo ${CONF_FILEPATH} foi configurado!"
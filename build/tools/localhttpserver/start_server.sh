#!/usr/bin/env bash

if [ -z "$ANDROID_PRODUCT_OUT" ]; then
  echo "\$ANDROID_PRODUCT_OUT don't defined, did you for setup and lunch Android build environment?"
  exit 1
fi

HTTP_BASE_DIR=$ANDROID_PRODUCT_OUT/http_dist
ASSETS_DIR=$HTTP_BASE_DIR/assets
if [ ! -d "$ASSETS_DIR" ]; then
  echo "Making assets directory..."
  mkdir -p "$ASSETS_DIR"
fi

declare -a DATA_FILES=(
  "product-info.json"
  "module-info.json"
  "module-deps.json"
  # Add more data files here.
)

# Copy data files to assets directory.
for i in "${DATA_FILES[@]}"
do
  if [ "$ANDROID_PRODUCT_OUT/$i" -nt "$ASSETS_DIR/$i" ]; then
    echo "Copy $ANDROID_PRODUCT_OUT/$i to $ASSETS_DIR/$i..."
    cp "$ANDROID_PRODUCT_OUT/$i" "$ASSETS_DIR/$i"
  fi
done

SERVER_HOST=localhost
SERVER_PORT=8000
URL=http://$SERVER_HOST:$SERVER_PORT

# Use default browser to open $URL.
OS=`uname`
if [ "$OS" = "Darwin" ]; then
  open $URL
elif [ "$OS" = "Linux" ]; then
  if which gnome-open > /dev/null
  then
    gnome-open $URL
  elif which xdg-open > /dev/null
  then
    xdg-open $URL
  fi
fi

# TODO: figure out an async approch to start server first and then open browser
# to avoid server not ready issue.

if [ "simple_http_server.py" -nt "$HTTP_BASE_DIR/simple_http_server.py" ]; then
  echo "Copy simple_http_server.py to $HTTP_BASE_DIR/simple_http_server.py ..."
  cp "simple_http_server.py" "$HTTP_BASE_DIR/simple_http_server.py"
fi

# Start local http server.
pushd "$HTTP_BASE_DIR" > /dev/null
python simple_http_server.py
popd > /dev/null

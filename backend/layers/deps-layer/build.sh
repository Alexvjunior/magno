#!/usr/bin/env bash
# Build deps-layer in a Lambda-compatible container, then publish it.
# Output zip: ./deps-layer.zip
set -euo pipefail

LAYER_NAME="claud-deps"
RUNTIME="python3.12"
HERE="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${HERE}/build/python"

rm -rf "${HERE}/build" "${HERE}/${LAYER_NAME}.zip"
mkdir -p "${BUILD_DIR}"

docker run --rm \
  -v "${HERE}":/work \
  -w /work \
  public.ecr.aws/sam/build-${RUNTIME}:latest \
  pip install -r requirements.txt -t build/python --no-cache-dir

(cd "${HERE}/build" && zip -r "../${LAYER_NAME}.zip" python)

echo "Built ${HERE}/${LAYER_NAME}.zip"
echo "Publish with:"
echo "aws lambda publish-layer-version --layer-name ${LAYER_NAME} \\"
echo "  --compatible-runtimes ${RUNTIME} \\"
echo "  --zip-file fileb://${HERE}/${LAYER_NAME}.zip"

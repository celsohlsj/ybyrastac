#!/usr/bin/env bash
# upload_to_source_coop.sh
# ========================
# Faz upload dos COGs locais para o Source Cooperative (S3-compatível).
#
# PRÉ-REQUISITOS:
#   1. Conta aprovada em https://source.coop (use @ipam.org.br ou @ufma.br)
#   2. Chaves S3 do dashboard Source Coop
#   3. aws cli instalado: pip install awscli  ou  conda install awscli
#
# USO:
#   export SOURCE_COOP_KEY="<ACCESS_KEY>"
#   export SOURCE_COOP_SECRET="<SECRET_KEY>"
#   bash scripts/ingestion/upload_to_source_coop.sh

set -euo pipefail

ENDPOINT="https://data.source.coop"
ORG="celsohlsj"          # nome da org no Source Coop
REPO="ybyra-br"          # nome do repositório
LOCAL_COG_ROOT="./cog"   # raiz local onde estão os COGs organizados por produto

AWS_CMD="aws s3"
AWS_OPTS="--endpoint-url ${ENDPOINT} \
          --no-sign-request \
          --region us-east-1"

# Configura credenciais temporariamente
export AWS_ACCESS_KEY_ID="${SOURCE_COOP_KEY}"
export AWS_SECRET_ACCESS_KEY="${SOURCE_COOP_SECRET}"
export AWS_DEFAULT_REGION="us-east-1"

upload_product() {
  local product="$1"   # ex.: fragmentation/ybyra-mspa-ma/v1.0
  local local_path="${LOCAL_COG_ROOT}/${product}"
  local s3_path="s3://source-coop/${ORG}/${REPO}/${product}/"

  echo ""
  echo "══════════════════════════════════════════════"
  echo "  Uploading: ${product}"
  echo "  De:  ${local_path}"
  echo "  Para: ${s3_path}"
  echo "══════════════════════════════════════════════"

  aws s3 cp "${local_path}" "${s3_path}" \
    --recursive \
    --endpoint-url "${ENDPOINT}" \
    --only-show-errors \
    --metadata "project=ybyra-br,producer=IPAM-UFMA,license=CC-BY-4.0"

  echo "✓ ${product} concluído"
}

# Produtos COG anuais
upload_product "fragmentation/ybyra-mspa-ma/v1.0"
upload_product "fragmentation/ybyra-mspa-br/v1.0"
upload_product "primary-forest/ybyra-primary-forest/v1.0"
upload_product "emissions/ybyra-emissions-brazil/v1.0"
upload_product "fire/ybyra-fire-probability-pa/v1.0"

# Produto Zarr (sync, preserva estrutura de diretórios do store)
echo ""
echo "══════════════════════════════════════════════"
echo "  Uploading Zarr store: secondary forest recovery"
echo "══════════════════════════════════════════════"
aws s3 sync \
  "${LOCAL_COG_ROOT}/recovery/ybyra-secondary-forest-recovery/v1.0/" \
  "s3://source-coop/${ORG}/${REPO}/recovery/ybyra-secondary-forest-recovery/v1.0/" \
  --endpoint-url "${ENDPOINT}" \
  --only-show-errors

echo ""
echo "✓ Upload completo para Source Cooperative."
echo "  URLs públicas: ${ENDPOINT}/${ORG}/${REPO}/"

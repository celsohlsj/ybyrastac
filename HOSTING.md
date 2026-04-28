# Onde hospedar os dados do YbYráSTAC (opções gratuitas)

Os dois componentes precisam de lugares distintos:

1. **Catálogo STAC (arquivos JSON) + browser visual** → leves (KB).
2. **Ativos pesados (COGs, Zarr)** → GB a TB.

## 1. Catálogo STAC + Browser — GitHub Pages (0 R$)

- Gratuito, 1 GB por repositório, 100 GB/mês de banda.
- JSONs do STAC ficam em `stac_catalog/` e o browser é publicado via Action
  (`.github/workflows/deploy-browser.yml`) em `celsohlsj.github.io/ybyrastac/`.
- Suporta CORS nativamente (ao contrário de muitos S3 sem configuração).

## 2. Ativos pesados — opções gratuitas comparadas

### ★ Source Cooperative (Radiant Earth) — *recomendação principal*

<https://source.coop>

- Organização sem fins lucrativos (Radiant Earth / Navigation Fund).
- **Gratuito para dados abertos** publicados por instituições de pesquisa.
- Infraestrutura AWS S3 real (URLs `https://data.source.coop/<org>/<repo>/...`).
- Já hospeda produtos de Maxar, VIDA, Protomaps, Earth Genome, Clark Univ.
- Feito para datasets em **formatos cloud-native** (COG, Zarr, GeoParquet, STAC).
- Suporta CORS, acesso anônimo, range-requests → funciona perfeitamente com
  `rioxarray.open_rasterio(url)` sem download.
- Escala TB sem problema. **Requer aplicação como beta-tester**
  (resposta típica em dias para instituições acadêmicas).
- **Melhor encaixe institucional**: IPAM + UFMA + GCBC se qualificam facilmente.

### Hugging Face Datasets

<https://huggingface.co/datasets>

- Gratuito até **1 TB** por usuário/organização (sem limite por arquivo até 50 GB).
- Infra Git LFS + Xet, URLs diretas, CORS OK.
- Originalmente pensado para ML, mas absolutamente funciona para rasters.
- *Contra*: discoverability fora de ML é menor; não é o "lugar certo" culturalmente.

### Zenodo (CERN)

<https://zenodo.org>

- Gratuito, **50 GB por depósito**, múltiplos depósitos possíveis.
- **Gera DOI** — ideal para citação em artigos (Nature Comm., etc.).
- *Contra*: otimizado para download, não streaming (não cloud-native por padrão;
  suporta range-requests em GeoTIFFs pequenos, mas COG não-nativo).
- **Uso recomendado**: publicar **snapshots versionados** (v1.0, v1.1...) com DOI,
  enquanto o Source Coop serve a versão "viva" para streaming.

### Cloudflare R2

<https://developers.cloudflare.com/r2/>

- **10 GB grátis + egress zero** (ilimitado).
- Compatível S3; funciona com `s3fs`, `rioxarray`, STAC.
- *Contra*: 10 GB é pouco para o YbYrá-BR inteiro (provavelmente 100 GB–2 TB).
- **Uso**: ótimo para **hospedar só os produtos do Maranhão** ou thumbnails
  e metadata (domínio custom `r2.ybyra-br.org`).

### AWS Open Data Sponsorship Program

<https://aws.amazon.com/opendata/open-data-sponsorship-program/>

- AWS paga 100% do armazenamento para datasets "de amplo interesse público".
- Mesma infra que MapBiomas, Sentinel, Landsat, etc.
- **Requer proposta formal** (pode levar meses). Ideal como passo 2
  depois do YbYrá-BR já ter tração.

### BDC-Lab (INPE)

<https://data.inpe.br/bdc/stac/v1/>

- Infraestrutura STAC institucional brasileira já rodando.
- Pode acomodar produtos YbYrá via parceria (seu ambiente de computação BDC-Lab
  já solicitado facilita).
- *Contra*: governança INPE, não 100% sob controle do YbYrá-BR.

## Recomendação prática (pipeline sugerido)

```
Produção local / BDC-Lab → COG / Zarr validados
        │
        ├──► Source Cooperative (streaming, URL pública, cloud-native)
        │
        ├──► Zenodo (snapshot versionado com DOI, 1x por release)
        │
        └──► GitHub Pages (só o catálogo STAC + browser)
```

**Custo total: R$ 0,00**.
Banda, egress, storage e CDN — todos cobertos pelos patrocinadores de cada
plataforma (AWS/Navigation Fund, CERN, GitHub).

## Configurando Source Coop (passo-a-passo)

1. Inscrever-se em <https://source.coop> (use e-mail institucional `@ipam.org.br`
   ou `@ufma.br`).
2. Solicitar organização `celsohlsj` ou `ybyra-br`.
3. Criar repositório `ybyra-br`.
4. Obter chaves S3 no dashboard.
5. Fazer upload com `aws s3 cp` ou `rclone`:

```bash
aws s3 cp ./cog/ s3://source-coop/celsohlsj/ybyra-br/fragmentation/ybyra-mspa-ma/v1.0/ \
    --recursive --endpoint-url https://data.source.coop
```

6. URLs ficam públicas automaticamente:
   `https://source.coop/ybyra-br/fragmentation/ybyra-mspa-ma/v1.0/ybyra-mspa-ma_2023.tif`

## Estimativa de volume para o YbYrá-BR

| Produto | Tamanho aprox. | Formato |
|---------|---------------|---------|
| MSPA-MA (39 anos, 30 m) | ~25 GB | COG uint8 |
| MSPA-BR (39 anos, 30 m) | ~600 GB | COG uint8 |
| Primary forest BR (39 anos) | ~150 GB | COG uint8 |
| Emissions BR (39 anos, 3 gases) | ~250 GB | COG float32 |
| Fire probability PA (1 km) | ~1 GB | COG float32 |
| Secondary recovery BR (2 cenários × 115 anos) | ~80 GB | Zarr float32 |
| **Total** | **~1.1 TB** | |

→ Entra folgado em **Source Cooperative** (sem limite prático para dados abertos).

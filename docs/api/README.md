# Albert API

## Execution locale

```bash
pip install -r requirements.txt
```
...or using `pyproject.toml` via a modern Python manager like [pip-tools](https://github.com/jazzband/pip-tools), [PDM](https://pdm.fming.dev/), [Poetry](https://python-poetry.org/docs/cli/#export) or [hatch](https://hatch.pypa.io/)


Lancer l'API dans le venv avec :
```bash
uvicorn app.main:app --reload
```

### Gpt4all quantized model (for CPUs)

To run the quantized model, the model `"{model-name}.bin"` needs to be imported/copied in `api/app`.

### Vllm model (for GPUs)

You must be registered with `huggingface-cli` to download private models:

```bash
huggingface-cli login --token $HF_ACCESS_TOKEN
```

### Download a model

#### Old version of deployment

- Fabrique model
```bash
python -c "from vllm import LLM; LLM(model='etalab-ia/fabrique-reference-2', download_dir='add_your_path')"
```
- Albert model
```bash
python -c "from vllm import LLM; LLM(model='etalab-ia/albert-light', download_dir='add_your_path')"
```

#### Newer version

Open python console
```bash
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/fabrique-reference-2'); tokenizer.save_pretrained('add_your_path/fabrique-reference-2'); model=AutoModelForCausalLM.from_pretrained('etalab-ia/fabrique-reference-2'); model.save_pretrained('add_your_path/fabrique-reference-2') "
```

```bash
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; tokenizer=AutoTokenizer.from_pretrained('etalab-ia/albert-light'); tokenizer.save_pretrained('add_your_path/albert-light'); model=AutoModelForCausalLM.from_pretrained('etalab-ia/albert-light'); model.save_pretrained('add_your_path/albert-light') "
```

## Tests unitaires de l'API

Lancer les test unitaires :
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing app/tests
```

Lancer l'API localement...
```bash
uvicorn app.main:app --reload
```

...puis les tests unitaires en parallèle dans un autre terminal :
```bash
python test.py
```

## Alembic

Create a new alembic (empty) template version:

    PYTHONPATH=. alembic revision -m  "vXXX

Autogenerate a new alembic upgrade version script:

    PYTHONPATH=. alembic revision --autogenerate -m "vXXX"

Upgrade a database according to alemic revision:

    PYTHONPATH=. alembic upgrade head


## Production

If GPU is available, the vllm API is run separately with:
```bash
python vllm_api.py --model etalab-ia/albert-light  --tensor-parallel-size 1 --gpu-memory-utilization 0.4 --port 8000
```

Run the public API:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8090 # --root-path /api/v2
    #gunicorn app.main:app  -w 2 -b 127.0.0.1:8090 --timeout 120
```


## Deploy

> En se placant à la racine du projet.

**Launch the reverse proxy**

This allows to route the incoming connections of the server. You can adapt the configuration file provided in [contrib/nginx](/contrib/nginx/).

To deploy over a https domain, you will need to : 
- adapt the hostnames to match yours in the conifg files (nginx config and app/config.py:CORS) and the following commands
- install lestencrypt/certbot: `sudo apt install certbot python3-certbot-nginx`
- run certbot to create and link the certificate to the server: 

```bash
sudo certbot -v --nginx --redirect -d ia.etalab.gouv.fr -d albert.etalab.gouv.fr --email language_model@data.gouv.fr
```

NOTE: If there is a firewall, certbot will struggle to complete the challenge to create the certificates as it requires a lestencript communication with the server (http).


**Launch the API database**

Launch Postgres container with:
```bash
docker-compose -f contrib/postgres/docker-compose up
```


**Launch the search engine services**

Launch Elasticsearch
```bash
docker-compose -f contrib/docker/elasticsearch/docker-compose.yml up
```

Launch qdrant
```bash
docker-compose -f contrib/docker/qdrant/docker-compose.yml up
```

Alternatively, with Docker only:

```bash
docker run --name elasticsearch -p 9202:9200 -p 9302:9300 -e discovery.type="single-node" -e xpack.security.enabled="false" -e ES_JAVA_OPTS="-Xms2g -Xmx2g" --mount source=vol-elasticsearch,target=/var/lib/elasticsearch/data -d docker.elastic.co/elasticsearch/elasticsearch:8.9.1
```
and
```bash
docker run --name qdrant -p 6333:6333 -p 6334:6334 --mount source=vol-qdrant,target=/qdrant/storage -d qdrant/qdrant:v1.5.0
```


**download the corpus**

    ./pyalbert.py download_corpus
    ./pyalbert.py download_directory


**build the chunks**

    ./pyalbert.py make_chunks --structured _data/data.gouv/


**build the embeddings matrix**

    ./pyalbert.py make_embeddings


**feed the search engines / build the indexes**

    # Elasticsearch indexes
    ./pyalbert.py index experiences --index-type bm25
    ./pyalbert.py index sheets --index-type bm25
    ./pyalbert.py index chunks --index-type bm25

    # Qdrant indexes (aka collections)
    ./pyalbert.py index experiences --index-type e5
    ./pyalbert.py index chunks --index-type e5


The search API and the RAG should now be ready to be used.

**set up the mail server**

    To be completed

**possibily migrate 


## Export pinned dependencies from pyproject.toml to requirements.txt

Using [PDM](https://pdm.fming.dev/)
```bash
pdm export --output requirements.txt --production --without-hashes
```

Using [Poetry](https://python-poetry.org/docs/cli/#export)
```bash
poetry export --without-hashes -f requirements.txt -o requirements.txt
```

Using [pip-tools](https://github.com/jazzband/pip-tools)
```bash
pip-compile --output-file requirements.txt requirements.in
```


################# OLD documentation
# API

> @obsolete since commit 6342af5
> See the openapi generated by fastapi instead.

### Fabrique LLM Routes

> **POST /api/fabrique**

Register configuration for "fabrique" text generation.

Headers:
```
Content-type: application/x-www-form-urlencoded  
```

Params:  
```
user_text(required): string : the user/civil experience to be answered
context: string : prompt information (need better doc @pclanglais ?)
institution: string : should be automatically added...
links: string : should be automatically added...
temperature: number between 0 and 1 : the orignalality of the answer (0: deterministic, 1: more creative)
```

Note: the answer result can then be obtained with `fabrique_stream`


> **GET /api/fabrique_stream**

Fabrique text answer generation.  
Server-sent stream like content.  
https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events


> **GET /api/fabrique_stop**

Stop a Fabrique text stream generation.

### Search Engines Routes

> **POST /api/search/{index}**

Search most relevant from a given {index}.

{index} can be:
- experiences: search the most relevant user experiences.
- sheets: search the most relevant sheets from service-public.fr.
- chunks: search the msot relevant chunks.

Headers:
```
Content-type: application/json
```

Params:  
```
q(required): string: search query
n(default=3): integer: max document to return
similarity(default=bm25) : string : similarity algorithm. Possible values : bm25, bucket, e5.
institution: string : Filter the search with the given institution (correspond to the field `intitule_typologie_1`) 
```

Returns: A Json list of result object ->  

For index=experiences:
```json
{
    "title" : "Title of the experience",
    "description" : "The user experience",
    "intitule_typologie_1" : "where it comes from"
    "reponse_structure_1" : "see https://opendata.plus.transformation.gouv.fr/explore/dataset/export-expa-c-riences/information"
}
```

For index=sheets
```json
{
    "title" : "Title of the sheet",
    "url" : "Url of the sheet",
    "introduction" : "Introduction of the sheet"
}
```

For index=chunks
```json
{
    "title" : "Title of the sheet",
    "url" : "Url of the sheet",
    "introduction" : "Introduction of the sheet"
    "text" : "The text part of the sheet (the chunk)"
    "context" : "The context of the chunk (successive chapter/sub-chapter/situation titles if any)"
}
```

### Misc

> **GET /api/institutions*

Get a list of known institutions.

Returns: A Json list of string.
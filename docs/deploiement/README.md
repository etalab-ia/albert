# Déploiement

Le projet Albert est composé de plusieurs services à déployer :
- pyalbert
- llm
- api
- embeddings

Pour cela vous devez d'abord disposer d'un environment répondant aux exigences requises ([Requirements](#requirements)). Puis deux installation sont possibles : sans Docker ([Installation locale (sans Docker)](#installation-locale-sans-docker)) ou avec ([Déploiement en CI/CD (avec Docker)](#déploiement-en-cicd-avec-docker)).

**Tables des matières**

[[_TOC_]]

## Requirements

Le projet est concçu pour fonctionner sur l'environnement Linux Ubuntu 22.04 LTS. De plus, les packages sont nécessaires :

* jq
* python3.10
* python3.10-venv
* nvidia-driver-535
* nvidia-cuda-toolkit
* nvidia-cuda-toolkit-gcc

*Pour docker :*
* nvidia-container-toolkit
* docker-ce
* docker-ce-cli
* containerd.io
* docker-buildx-plugin
* docker-compose-plugin

Pour un déploiement en production vous pouvez utiliser le script [init_vm.sh](../../utils/init_vm.sh) pour configurer l'environnement nécessaire au projet Albert. Copiez le script sur le serveur et exécutez la commande suivante :

```bash
bash ./init_vm.sh
```

Ce script permet d'installer les packages nécessaires ainsi que de créer un utilisateur *gitlab* qui sera nécessaire pour le déploiement de la pipeline de CI/CD. Pour exécuter le script il est nécessaire d'exporter préalablement les variables suivantes :
* `GITLAB_PASSWORD` (mot de passe de l'utilisateur *gitlab*)
* `GITLAB_SSH_PUBLIC_KEY` (clef public qui sera ajouté à l'utilisateur *gitlab*)

## Installation locale (sans Docker)

* Clonez le repository

	```bash
	git clone git@gitlab.com:etalab-datalab/llm/albert-backend.git ~/albert-backend && cd ~/albert-backend
	```

* Créez un environnement virtuel python et l'activer

	```bash
	mkdir ~/albert && python3 -m venv ~/albert && source ~/albert/bin/activate
	```

	> ⚠️ Vous devez créer cet environment avec Python 3.10.

### Pyalbert 

* Installez les packages nécessaires

	```bash
	pip install -r ./pyalbert/requirements.txt
	```

* Ajoutez pyalbert aux librairies de votre environment virtuel

	```bash
	ln -s ./pyalbert albert/lib/python3.10/site-packages
	```

	> ⚠️ Remplacez la version de Python par celle correspondante à votre environment si celle-ci n'est pas 3.10.

### LLM


* Installez les packages nécessaires

	```bash
	pip install -r ./llm/vllm/requirements.txt
	pip install -r ./llm/gpt4all/requirements.txt
	```

* Lancer un modèle

	Le script [launch_local_llm.sh](../../utils/launch_local_llm.sh) permet de télécharger et lancer l'API d'un modèle Albert en une seule ligne de commande. Vous pouvez déployer un modèle avec deux drivers : vllm ou gpt4all. Pour plus d'information, rendez vous sur la documentation [models.md](../models.md) qui détaille la configuration des différents modèles Albert disponibles.
 
	```bash
	bash ./utils/launch_local_llm.sh \
	-s STORAGE_PATH \
	-r HF_REPO_ID \
	-p PORT \
	-d DRIVER
	```

	Par exemple pour lancer [tiny-albert](https://huggingface.co/AgentPublic/tiny-albert) :

	```bash
	bash ./utils/launch_local_llm.sh -s ~/models -r AgentPublic/tiny-albert -d gpt4all -p 8000 -m ggml-model-expert-q4_K.bin
	```

	Ou encore pour lancer [albert-light](https://huggingface.co/AgentPublic/albert-light) :

	```bash
	bash ./utils/launch_local_llm.sh -s ~/models -r AgentPublic/albert-light -d vllm -p 8000
	```

### Reverse proxy (Nginx)

* Installez Nginx

	```bash
	sudo apt install nginx
	```

* Configurez Nginx pour rediriger les requêtes vers l'API, activez le vhost et redémarrez Nginx:

	```bash
	sudo cp ./contrib/nginx/albert.conf /etc/nginx/sites-available/albert.conf
	sudo ln -s /etc/nginx/sites-available/albert /etc/nginx/sites-enabled
	sudo systemctl restart nginx
	```

* Installez certbot

	```bash
	sudo apt install certbot python3-certbot-nginx
	```

* Créez un certificat SSL pour votre domaine

	```bash
	sudo certbot --nginx -d mondomaine.com
	```

	Vous pouvez ensuite vérifier que le certificat a été correctement installé en regardant si le fichier `/etc/nginx/sites-available/albert.conf` a bien été modifié:
	```bash
	cat /etc/nginx/sites-available/albert.conf
	```

* Optionnel : installez et configurez le firewall pour Nginx

	```bash
	sudo apt install ufw
	sudo ufw allow 'Nginx Full'
	sudo ufw allow ssh # très important! pour conserver sa connection ssh
	sudo ufw enable
	```

* Optionnel : n'oubliez pas d'installer et d'activer fail2ban

	```bash
	sudo apt install fail2ban
	sudo systemctl start fail2ban # pour le démarrer
	sudo systemctl enable fail2ban # pour le démarrer au démarrage
	```

### Databases

* Créer un fichier de variable d'environnement avec les variables suivantes :

	* `POSTGRES_PASSWORD`
    * `POSTGRES_PORT`
    * `ELASTIC_PASSWORD`
  	* `ELASTIC_PORT`
    * `QDRANT_PORT`
    * `COMPOSE_FILE`
    * `COMPOSE_PROJECT_NAME`

	Pour plus d'informations sur la valeur des variables voir la documentation dédiées [environments.md](environments.md).

	Les variables `COMPOSE_FILE` et `COMPOSE_PROJECT_NAME` sont des variables prédéfinies par Docker, pour plus d'information voir la [documentation officielle]( https://docs.docker.com/compose/environment-variables/envvars/).


* Déployer les bases de données

	```bash
	docker compose --env-file=PATH_TO_ENV_FILE down && docker compose --env-file=PATH_TO_ENV_FILE up --detach
	```

### API

#### Avec docker

* Exportez les variables d'environnement suivantes :

	* `POSTGRES_PASSWORD`
    * `POSTGRES_PORT`
    * `POSTGRES_HOST`


## Installation avec Docker

L'installation avec Docker se fait dans le cadre d'un pipeline de CI/CD Gitlab. Reférez-vous au fichier [.gitlab-ci.yml](../../.gitlab-ci.yml) pour plus d'information sur les étapes de déploiement réalisée. Afin d'exécuter cette pipeline il est nécessaire de configurer au préalable certaines variables d'environnement dans Gitlab. Pour cela rendez vous sur la documentation [environments.md](environments.md).

Les étapes de CI/CD (dupliquées pour chaque environnement) sont décrites schématiquement ici :

```mermaid
---
title: "Albert deployment flow"
---
graph TD

subgraph VLLM["VLLM"]
    job_vllm_build["build"]
    -.-> job_vllm_setup["setup\n[pyalbert/albert.py]\ndownload_models"]
    -.-> job_vllm_deploy["deploy\n(manual)"]
    -.-> job_vllm_test["test"]
end

subgraph API["API"]
    job_api_build["build"]
    -.-> job_api_setup["setup\n[pyalbert/albert.py]\ncreate_whitelist"]
    -.-> job_api_deploy["deploy\n(manual)"]
    -.-> job_api_test["test"]

end

job_pre["link gpu"]
job_post["unlink gpu"]

job_pre -.-> |"only staging"| VLLM
job_pre -.-> |"only staging"| API
VLLM -.-> |"only staging"| job_post
API -.-> |"only staging"| job_post
```

* Configurez les modèles à déployer dans le fichier [llm_routing_table.json](../../pyalbert/config/llm_routing_table.json)

	Pour plus d'information sur comment configurer ce fichier, rendez vous sur la documentation [models.md](../models.md) qui détaille la configuration des différents modèles disponibles.

* Téléchargez les modèles spécifiez dans le fichier de configuration

	```bash
	python albert-backend/pyalbert/albert.py download_model --storage-dir=STORAGE_PATH --hf-repo-id=
	```

	> 💡 Remplacez STORAGE_PATH par l'emplacement où vous souhaitez stocker les modèles et ENV par la valeur que vous avez mentionnée dans le fichier de configuration.

#!/bin/bash
set -e

Help()
{
   # Display Help
   echo "Dynamic deploy api containers."
   echo
   echo "Syntax: bash build.sh [-h|r|d|e]"
   echo "options:"
   echo "h          display this help and exit"
   echo "r          path to routing table file"
   echo "e          CI environment name. Only services in routing table with this CI environment will be deployed. If not specified, all services will be deployed"
}

while getopts "hr:e:" flag
do
    case "${flag}" in
        h)  Help && exit 1;;
        r)  routing_table=${OPTARG};;
        e)  ci_environment_name=${OPTARG};;
    esac
done

if [[ -z $routing_table ]]; then
    echo "-r argument is required. Help:" && Help && exit 0
elif ! [[ -f $routing_table ]]; then
    echo "file specified with -r argument does not exists. Help:" && Help && exit 0
fi

for model in $(jq -r 'keys[]' $routing_table); do

    host=$(jq -r '.["'$model'"] | .llm_host' $routing_table)
    if [[ $host != "${CI_DEPLOY_HOST}" ]] && [[ $host != "all" ]]; then
        echo "info: skip model $model (host: $host)"
        continue
    fi

    api_port=$(jq -r '.["'$model'"] | .api_port' $routing_table)

    if [[ $api_port = "null" ]]; then
        echo "error: api_port is required for $model. Skipping api-v2 container" && exit 1
    fi

    if [[ -z $port_list ]]; then
        port_list=$api_port

    elif ! [[ $port_list =~ (^|[[:space:]])$api_port($|[[:space:]]) ]]; then
        port_list="$port_list $api_port"
    else
        continue
    fi

    for model in $(jq -r 'keys[]' $routing_table); do

        llm_host=$(jq -r '.["'$model'"] | .llm_host' $routing_table)
        if [[ $llm_host != "${CI_DEPLOY_HOST}" ]] && [[ $llm_host != "all" ]]; then
            echo "info: skip model $model (host: $llm_host)"
            continue
        fi

        llm_port=$(jq -r '.["'$model'"] | .llm_port' $routing_table)
        llm_hf_repo_id=$(jq -r '.["'$model'"] | .llm_hf_repo_id' $routing_table)
        current_api_port=$(jq -r '.["'$model'"] | .api_port' $routing_table)

        if [[ $llm_port = "null" ]] || [[ $llm_host = "null" ]] || [[ $llm_hf_repo_id = "null" ]]; then
            echo "error: llm_port, llm_host, llm_hf_repo_id are required for $model. Skipping api-v2 container" && exit 1
        fi

        if [[ $api_port == $current_api_port ]]; then
            if [[ -z $model_list ]]; then
                model_list="(\"$llm_hf_repo_id\", \"http://${llm_host}:${llm_port}\")"
            else
                model_list="$model_list, (\"$llm_hf_repo_id\", \"http://${llm_host}:${llm_port}\")"
            fi
        else
            continue
        fi
        
    done
    
    model_list="[${model_list}]"
    api_table+=("($api_port, $model_list)")
    unset model_list

done

# for i in range length of api_table
for (( i=0; i<${#api_table[@]}; i++ ));do
    api_port=$(echo ${api_table[$i]} | cut -d',' -f1 | tr -d '()' | tr -d '[:space:]')
    echo "info: api_port: $api_port"
    # get index of the first "[" character in ${api_table[$i] and store it in a variable
    start_index=$(echo ${api_table[$i]} | grep -aob '\[' | head -n1 | cut -d: -f1)
    # get string from start_index to the end of the string
    model_list=$(echo ${api_table[$i]} | cut -c$(($start_index+1))- | rev | cut -c 2- | rev)

    export COMPOSE_PROJECT_NAME=$ci_environment_name
    export LLM_TABLE=$model_list
    export API_PORT=$api_port
    echo "info: LLM_TABLE: $LLM_TABLE"

    echo "info: deploying ${COMPOSE_PROJECT_NAME}-${API_PORT}-api-v2 container"
    docker container rm --force ${COMPOSE_PROJECT_NAME}-${API_PORT}-api-v2 || true
    docker image rm ${CI_REGISTRY_IMAGE}/api:${CI_API_IMAGE_TAG} || true
    
    docker run --gpus all --detach --publish ${API_PORT}:8090 --restart always --name ${COMPOSE_PROJECT_NAME}-${API_PORT}-api-v2 \
    --env-file .env \
    --env API_URL=${CI_DEPLOY_URL} \
    --env FRONT_URL=${CI_DEPLOY_URL} \
    --env "LLM_TABLE=${LLM_TABLE}" \
    ${CI_REGISTRY_IMAGE}/api:${CI_API_IMAGE_TAG}
done

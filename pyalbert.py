#!/bin/python

""" Manage the Legal Information Assistant.

Usage:
    pyalbert.py download_corpus
    pyalbert.py download_directory
    pyalbert.py make_chunks [--structured] [--chunk-size N] [--chunk-overlap N] [DIRECTORY]
    pyalbert.py make_questions [DIRECTORY]
    pyalbert.py make_embeddings
    pyalbert.py index (experiences | sheets | chunks) [--index-type=INDEX_TYPE] [--recreate] [DIRECTORY]
    pyalbert.py finetune MODEL VERSION
    pyalbert.py evaluate MODEL VERSION [-n N] [-y] [--csv]
    pyalbert.py evaluate -o OUTPUT (--merge MODEL VERSION)...

Commands:
    download            Download the given source of data. Downloaded data should consitute the inputs for the further processing steps.

    download_directory  Download official directorier to build whitelists. Files are stored under _data/directory/.

    make_chunks     Parse les fichiers XML issue de data.gouv (fiches service publique), situé dans le repertoir DIRECTORY pour les transformer en fiches sous format Json.
                    Chaque élement Json correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.
                    Chunks are created under _data/sheets_as_chunks.json.

    make_questions  Create a corpus of questions from the XML SP sheets.

    make_embeddings Build the embeddings matrix to be used with e5 index.

    index           Create the given index to search relevant document given a query. Each index is created using a specific file as ground-truth.
                    See doc to see which files are used by which index.

    finetune        (NOT IMPLEMENTED) Fine-tune the given model. Parameters will be read from fine_tuning/x/{MODEL}-{VERSION}/.
                    Results will be saved in _data/x/{MODEL}-{VERSION}.

    evaluate        Run evaluation for the given llm model.
                    Results will be saved in _data/x/{MODEL}-{VERSION}.
                    if --merge is used, a json containing the list of prompts + generations under _data/{p,x} directory will be saved
                    using the the list of the {MODEL-VERSION} couples given.


Options:
    --chunk-size N           The maximum size of the chunks (token count...) [default: 1100]
    --chunk-overlap N        The size of the overlap between chunks [default: 200]
    --index-type INDEX_TYPE  The type of index to create (bm25, bucket, e5) [default: bm25]
    --size N, -n N           Limit the number of generations/inferences.
    --output OUTPUT, -o OUTPUT    A ouput name, to save result to.
    --yes, -y                assumes yes for every user input question.
    --csv                    Make a csv table
    --recreate               Force collection/index recreation


Examples:
    ./pyalbert.py download_directory
    ./pyalbert.py make_chunks --chunk-size 500 --chunk-overlap 20
    ./pyalbert.py make_chunks --structured
    ./pyalbert.py make_questions _data/data.gouv/
    !make institutions          # Generate the french institution list
    ./pyalbert.py index experiences  # assumes _data/export-expa-c-riences.json exists
    ./pyalbert.py index sheets       # assumes _data/data.gouv/ + _data/fiches-travail.json exist
    ./pyalbert.py index chunks       # assumes _data/sheets_as_chunks.json + _data/fiches-travail.json exist
    ./pyalbert.py evaluate miaou v0  # Run the inference
    ./pyalbert.py evaluate miaou v0 --csv  # make an result table with inference file found in data/x/{model}-{version}
    ./pyalbert.py evaluate --merge albert-light-simple v0 --merge albert-light-rag v0 -o albert-light-v0
"""


from docopt import docopt

try:
    from app.config import SHEET_SOURCES
except ModuleNotFoundError:
    from api.app.config import SHEET_SOURCES

if __name__ == "__main__":
    # Parse CLI arguments
    args = docopt(__doc__, version="0")

    if not args["DIRECTORY"]:
        args["DIRECTORY"] = "_data/data.gouv/"

    # Run command
    if args["download_corpus"]:
        from sourcing import download_corpus

        download_corpus()
    elif args["download_directory"]:
        from sourcing import create_whitelist, download_directory

        download_directory()
        create_whitelist()
    elif args["make_chunks"]:
        from sourcing import make_chunks

        make_chunks(
            args["DIRECTORY"],
            structured=args["--structured"],
            chunk_size=int(args["--chunk-size"]),
            chunk_overlap=int(args["--chunk-overlap"]),
            sources=SHEET_SOURCES,
        )
    elif args["make_questions"]:
        from sourcing import make_questions

        make_questions(args["DIRECTORY"])
    elif args["make_embeddings"]:
        from ir import make_embeddings

        make_embeddings()

    elif args["index"]:
        from ir import create_index

        indexes = ["experiences", "chunks", "sheets"]
        for name in indexes:
            if name in args and args[name]:
                create_index(
                    args["--index-type"],
                    name,
                    recreate=args["--recreate"],
                    directory=args["DIRECTORY"],
                )
    elif args["finetune"]:
        raise NotImplementedError
    elif args["evaluate"]:
        from evaluation import evaluate, merge_eval

        if args.get("--merge", 0) == 0:
            # run evaluation
            evaluate(
                args["MODEL"][0],
                args["VERSION"][0],
                limit=args["--size"],
                yes=args["--yes"],
                to_=args["--csv"],
            )
        else:
            # Merge evaluation results into a final json file
            merge_eval(args["MODEL"], args["VERSION"], args["--output"])
    else:
        raise NotImplementedError
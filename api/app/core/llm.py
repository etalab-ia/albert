from commons import get_prompter, get_llm_client

from app import crud, schemas
from app.db.session import SessionLocal


def auto_set_chat_name(chat_id: int, stream: schemas.StreamCreate) -> str | None:
    with SessionLocal() as db:
        model_name = stream.model_name
        query = " ".join(stream.query.split(" ")[:512])  # 512 words should be sufficient to title the query

        # Build prompt
        query = f"Synthétise la demande suivante en un court titre de quelque mots (pas plus de 8 mots) permettant d'identifier la thématique. Le titre doit être court, clair et accrocheur:\n\n{query}"
        prompter = get_prompter(model_name)
        prompt = prompter.make_prompt(query=query)

        # Generate
        llm_client = get_llm_client(prompter.url)
        chat_name = llm_client.generate(prompt, temperature=20)

        # Update db_chat
        db_chat = crud.chat.get_chat(db, chat_id)
        if not db_chat:
            return

        db_chat.chat_name = chat_name
        db.commit()
        return chat_name

#!/bin/python

import os
import shutil
import sys

import bitsandbytes as bnb
import numpy as np
import torch
from datasets import concatenate_datasets, load_dataset
from peft import (AutoPeftModelForCausalLM, LoraConfig, PeftModel,
                  get_peft_model)
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, HfArgumentParser,
                          LlamaTokenizerFast, TrainingArguments, logging,
                          pipeline)
from trl import SFTTrainer

sys.path.append(".")

from commons.prompt import format_llama_chat_prompt

# @EXPLORE techniques to make training better, stronger, faster :
# - FlashAttention: https://arxiv.org/abs/2307.08691
# - DeepSpeed: https://github.com/microsoft/DeepSpeed
# - Self-chat ? : https://arxiv.org/abs/2304.01196
# -> Also Mentioned in **Vigogne**: https://github.com/bofenghuang/vigogne

# @TEST:
# Add an eval dataset !
# target_modules=["q_proj", "v_proj"] -> what does None here ????
# target_modules=["q_proj", "up_proj", "o_proj", "k_proj", "down_proj", "gate_proj", "v_proj"]
# lr_scheduler_type = cosine
# different dopout/optim/gradient_accumulation_steps(==[1,2,3]?) ?
# use 8bit quantization

# @CHANGES from fabrique
# - learning rate was 2e-4
# - batch_size was 3
# - max_step was 4001
# - gradient_accumulation_steps was 4

#
# Utils
#


# SOURCE https://github.com/artidoro/qlora/blob/main/qlora.py
def find_all_linear_names(model):
    cls = (
        bnb.nn.Linear4bit
    )  # if args.bits == 4 else (bnb.nn.Linear8bitLt if args.bits == 8 else torch.nn.Linear)
    lora_module_names = set()
    for name, module in model.named_modules():
        if isinstance(module, cls):
            names = name.split(".")
            lora_module_names.add(names[0] if len(names) == 1 else names[-1])

    if "lm_head" in lora_module_names:  # needed for 16-bit
        lora_module_names.remove("lm_head")
    return list(lora_module_names)


#
# 1. Parametrization
#

model_name = "NousResearch/Llama-2-13b-chat-hf"  # Base model
new_model_name = "albert-light-v0"  # new model name
output_dir = f"_data/models/{new_model_name}"  # The output directory where the model predictions and checkpoints will be written
output_merged_dir = os.path.join(output_dir, new_model_name, new_model_name)
tb_log_dir = f"{output_dir}/logs"  # Tensorboard logs

# Training parameters !
max_seq_length = 2048  # C'est la fenêtre contextuelle. Elle peut être portée jusqu'à 4096 tokens (mais attention à la mémoire disponible !)
per_device_train_batch_size = (
    12  # Nombre d'exemples envoyés par batch. En mettre plus pour aller plus vite.
)
learning_rate = 1e-4  # De préférence un taux d'apprentissage élevé pour un texte en français (depends also of the batch size)
save_steps = 200  # Sauvegarde des steps (permet de faire redémarrer l'entraînement si le fine-tuning ne fonctionne pas)
lr_scheduler_type = "constant"  # Learning rate schedule (constant a bit better than cosine, and has advantage for analysis)
gradient_accumulation_steps = 2
max_grad_norm = 0.3
lora_r = 64  # dimension of the updated matrices
lora_alpha = 16  # parameter for scaling
lora_dropout = 0.1  # dropout probability for layers
group_by_length = True  # Group sequences into batches with same length (saves memory and speeds up training considerably)
warmup_ratio = 0.03  # Fraction of steps to do a warmup for
optim = "paged_adamw_32bit"  # Optimizer to use, original is paged_adamw_32bit
logging_steps = 10  # Log every X updates steps

# To adjust given the traning size and epoch number
# max_steps = 4001 # overrides num_train_epochs
num_train_epochs = 1

# Unused ?
local_rank = -1
per_device_eval_batch_size = 1
weight_decay = 0.001
gradient_checkpointing = True  # Enable gradient checkpointing

# Quantization
use_4bit = True  # Activate 4-bit precision base model loading
use_nested_quant = False  # Activate nested quantization for 4-bit base models
bnb_4bit_compute_dtype = "float16"  # Compute dtype for 4-bit base models
bnb_4bit_quant_type = "nf4"  # Quantization type (fp4 or nf4)
compute_dtype = getattr(torch, bnb_4bit_compute_dtype)

fp16 = True  # Enable fp16 training
bf16 = False  # Enable bf16 training

# Use dataset packing
packing = False

# Load the entire model on the GPU 0
device_map = {"": 0}

# Visualize training
report_to = "tensorboard"

#
# 2. Load training data
#

np.random.seed(42)

def from_conversation(item):
    prompt = item["conversation"][0]["content"]
    answer = item["conversation"][1]["content"]
    return {"prompt": prompt, "answer": answer}


# dataset = load_dataset("databricks/databricks-dolly-15k", split="train")
datasets = {
    "chatgpt_rag": {"path": "_data/training_albert-light.json", "n_samples": 1000},
    "alpaca": {"path": "_data/converted_alpaca_data_cleaned_fr_52k.jsonl", "n_samples": 300},
    "dolly": {"path": "_data/converted_dolly_bactrian_fr_15k.jsonl", "n_samples": 300},
}
datasets_l = []
for dataset_name, d in datasets.items():
    data = load_dataset("json", data_files=d["path"], split="train")
    data = data.select(np.random.choice(len(data), size=d["n_samples"], replace=False))
    if dataset_name in ["alpaca", "dolly"]:
        data = data.map(from_conversation, remove_columns=data.column_names)
    datasets_l.append(data)
data = concatenate_datasets(datasets_l)
data = data.map(format_llama_chat_prompt)
data = data.shuffle(seed=42)
dataset = data.train_test_split(test_size=0.1, shuffle=True, seed=42)
train_data = dataset["train"]
eval_data = dataset["test"]


#
# 3. Load model and tokenizer
#

tokenizer = LlamaTokenizerFast.from_pretrained(
    model_name, padding_side="left", add_eos_token=True, add_bos_token=True, use_fast=False
)
tokenizer.pad_token = tokenizer.eos_token  # llama2 seems to require that...

# Load tokenizer and model with QLoRA configuration
bnb_config = BitsAndBytesConfig(
    load_in_4bit=use_4bit,
    bnb_4bit_quant_type=bnb_4bit_quant_type,
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=use_nested_quant,
)

if compute_dtype == torch.float16 and use_4bit:
    major, _ = torch.cuda.get_device_capability()
    if major >= 8:
        print("=" * 80)
        print("Your GPU supports bfloat16, you can accelerate training with the argument --bf16")
        print("=" * 80)

model = AutoModelForCausalLM.from_pretrained(
    model_name, device_map=device_map, quantization_config=bnb_config
)

model.config.use_cache = False
model.config.pretraining_tp = 1

#
# 4. Fine-tuning
#

os.makedirs(output_dir, exist_ok=True)

training_arguments = TrainingArguments(
    output_dir=output_dir,
    per_device_train_batch_size=per_device_train_batch_size,
    gradient_accumulation_steps=gradient_accumulation_steps,
    optim=optim,
    save_steps=save_steps,
    logging_steps=logging_steps,
    learning_rate=learning_rate,
    fp16=fp16,
    bf16=bf16,
    max_grad_norm=max_grad_norm,
    # max_steps=max_steps,
    num_train_epochs=num_train_epochs,
    warmup_ratio=warmup_ratio,
    group_by_length=group_by_length,
    lr_scheduler_type=lr_scheduler_type,
    report_to=report_to,
)

# Lora/peft config
peft_config = LoraConfig(
    lora_alpha=lora_alpha,
    lora_dropout=lora_dropout,
    r=lora_r,
    inference_mode=False,
    task_type="CAUSAL_LM",
    target_modules=find_all_linear_names(model),
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    tokenizer=tokenizer,
    args=training_arguments,
    packing=packing,
)

trainer.train(resume_from_checkpoint=True)

#
# 5. Save Lora weigts
#

model_to_save = (
    trainer.model.module if hasattr(trainer.model, "module") else trainer.model
)  # Take care of distributed/parallel training
model_to_save.save_pretrained(new_model_name)


#
# 6. Merged...
#

# Free memory for merging weights
del model
del trainer
torch.cuda.empty_cache()

model = AutoPeftModelForCausalLM.from_pretrained(
    new_model_name, device_map="auto", torch_dtype=torch.bfloat16
)
model = model.merge_and_unload()
model.save_pretrained(output_merged_dir, safe_serialization=True)
# On récupère le tokenizer pour l'inférence
# @FIX: how to do that in a clean way ?
# shutil.copyfile(
#    "/home/planglais/llama/llama-2-13b-hf/tokenizer.model", output_merged_dir + "/tokenizer.model"
# )
# shutil.copyfile(
#    "/home/planglais/llama/llama-2-13b-hf/special_tokens_map.json",
#    output_merged_dir + "/special_tokens_map.json",
# )
# shutil.copyfile(
#    "/home/planglais/llama/llama-2-13b-hf/tokenizer_config.json",
#    output_merged_dir + "/tokenizer_config.json",
# )
tokenizer.save_pretrained(output_merged_dir)

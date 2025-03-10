import json
from datasets import load_dataset
from transformers import GPT2Tokenizer, GPT2LMHeadModel, Trainer, TrainingArguments, DataCollatorForLanguageModeling

# Load dataset and split into train/eval sets
dataset = load_dataset('json', data_files='bot/lingolizard_data.jsonl', split="train")
dataset = dataset.train_test_split(test_size=0.1)  # 90% train, 10% eval

train_dataset = dataset["train"]
eval_dataset = dataset["test"]

# Initialise tokenizer and model
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Fix padding issue
tokenizer.pad_token = tokenizer.eos_token  

# Tokenise dataset
def tokenise_function(examples):
    return tokenizer(examples['prompt'] + examples['completion'], padding="max_length", truncation=True, max_length=512)

train_dataset = train_dataset.map(tokenise_function, batched=True, remove_columns=["prompt", "completion"])
eval_dataset = eval_dataset.map(tokenise_function, batched=True, remove_columns=["prompt", "completion"])

# Data collator
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    overwrite_output_dir=True,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    save_steps=10_000,
    save_total_limit=2,
    eval_strategy="steps",  # Enables evaluation
    eval_steps=500,
    logging_steps=100,
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,  # Now we pass eval dataset
)

# Train the model
trainer.train()

# Save the model
trainer.save_model("./trained_model")

# Save the tokenizer
tokenizer.save_pretrained("./trained_model")

import json
import torch
from datasets import Dataset
from transformers import (
    T5Tokenizer, 
    T5ForConditionalGeneration, 
    Seq2SeqTrainer, 
    Seq2SeqTrainingArguments, 
    DataCollatorForSeq2Seq
)

# --- CONFIG ---
MODEL_ID = "google/flan-t5-base"
DATA_FILE = "synthetic_resume_data.json"
OUTPUT_DIR = "./fine_tuned_models/nlp"

def train():
    # 1. Load Data
    print(f"Loading data from {DATA_FILE}...")
    with open(DATA_FILE, "r") as f:
        raw_data = json.load(f)
    
    dataset = Dataset.from_list(raw_data)
    
    # 2. Initialize Tokenizer & Model
    tokenizer = T5Tokenizer.from_pretrained(MODEL_ID)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_ID)

    # 3. Preprocessing
    def preprocess_function(examples):
        inputs = examples["text"]
        targets = examples["target"]
        
        # Tokenize inputs
        model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding="max_length")
        
        # Tokenize targets
        labels = tokenizer(targets, max_length=512, truncation=True, padding="max_length")
        
       
        labels["input_ids"] = [
            [(l if l != tokenizer.pad_token_id else -100) for l in label] for label in labels["input_ids"]
        ]
        
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    print("Tokenizing dataset...")
    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    # 4. Training Arguments
    args = Seq2SeqTrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=4, # Lower this if you get Out of Memory errors
        num_train_epochs=3,
        save_strategy="epoch",
        logging_steps=10,
        learning_rate=1e-4,
        predict_with_generate=True
    )

    # 5. Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)
    )

    # 6. Run Training
    print("Starting training...")
    trainer.train()

    # 7. Save Final Model
    print(f"Saving fine-tuned model to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Done! You can now use this path in your Django extract_insights.py")

if __name__ == "__main__":
    train()
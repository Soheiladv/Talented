from transformers import GPT2LMHeadModel, GPT2Tokenizer, pipeline

local_model_path = "./bolbolzaban"

tokenizer = GPT2Tokenizer.from_pretrained(local_model_path)
model = GPT2LMHeadModel.from_pretrained(local_model_path)

generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=256,
    device=-1  # GPU=0
)

prompt = "در یک اتفاق شگفت انگیز، پژوهشگران"
result = generator(prompt, num_return_sequences=1)
print(result[0]["generated_text"])

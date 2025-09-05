from huggingface_hub import InferenceClient

client = InferenceClient()
models = client.list_deployed_models(frameworks="text-generation-inference")
print(models.get("text-generation", []))

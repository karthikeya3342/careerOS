from cascadeflow import ModelConfig

print("ModelConfig Pydantic fields:")
for name, field in ModelConfig.model_fields.items():
    print(f"  {name}: annotation={field.annotation}, default={field.default}, required={field.is_required()}")

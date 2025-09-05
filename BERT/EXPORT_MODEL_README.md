# Exporting and Using JointBERT Models

This guide explains how to export your trained JointBERT model for use in other applications.

## Exporting a Trained Model

After training your model (e.g., the snips_model), you can export it using the provided `export_model.py` script:

```bash
python export_model.py \
    --model_dir /path/to/your/trained/model \
    --output_dir /path/to/export/model
```

For example, if you trained a model for the SNIPS dataset:

```bash
python export_model.py \
    --model_dir ./snips_model \
    --output_dir ./exported_snips_model
```

This will export the following components to the specified output directory:

1. The model weights and configuration
2. The tokenizer files
3. The intent and slot label mappings (as JSON files)
4. The training arguments
5. Model metadata (model type, task, max sequence length, etc.)

## Using the Exported Model in Other Applications

You can use the exported model in other applications with the provided `use_exported_model.py` script. This script demonstrates how to load and use the model for inference.

### Interactive Mode

To interactively test the model:

```bash
python use_exported_model.py \
    --model_dir ./exported_snips_model \
    --interactive
```

This will start an interactive session where you can enter text and see the predicted intent and slots.

### Batch Processing

To process a file containing multiple sentences (one per line):

```bash
python use_exported_model.py \
    --model_dir ./exported_snips_model \
    --input_file input.txt \
    --output_file results.json
```

## Integrating into Your Own Application

To integrate the exported model into your own application, follow these steps:

1. **Load the model and related components**:
   ```python
   from use_exported_model import load_exported_model, predict_intent_and_slots
   
   # Load model and related components
   model, tokenizer, intent_label_lst, slot_label_lst, device, metadata = load_exported_model("./exported_snips_model")
   ```

2. **Make predictions**:
   ```python
   # Make predictions
   text = "turn on the kitchen lights"
   result = predict_intent_and_slots(text, model, tokenizer, intent_label_lst, slot_label_lst, device, metadata)
   
   print(f"Intent: {result['intent']}")
   print("Slots:")
   for word, slot in result['slots']:
       print(f"  {word}: {slot}")
   ```

## Model Format

The exported model follows the Hugging Face Transformers format, which means you can also load it directly using the Transformers library if you implement the necessary model class.

## Requirements

To use the exported model, you'll need:

- PyTorch
- Transformers library
- The same version of the libraries used during training

You can install the required packages using:

```bash
pip install -r requirements.txt
```

## Deployment Considerations

When deploying the model in production:

1. Consider quantizing the model to reduce its size and improve inference speed
2. For web applications, you might want to use ONNX Runtime or TorchScript for better performance
3. For mobile applications, consider using TensorFlow Lite or PyTorch Mobile

## Troubleshooting

If you encounter issues when loading the exported model:

1. Ensure you're using the same version of PyTorch and Transformers as during training
2. Check that all required files are present in the export directory
3. Verify that the model type and configuration match what was used during training
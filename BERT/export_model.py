import os
import logging
import argparse
import torch
import json

from utils import init_logger, load_tokenizer, get_intent_labels, get_slot_labels, MODEL_CLASSES

logger = logging.getLogger(__name__)


def get_args(model_dir):
    return torch.load(os.path.join(model_dir, 'training_args.bin'), weights_only=False)


def export_model(args):
    init_logger()
    
    # Load the trained model arguments
    model_args = get_args(args.model_dir)
    
    # Get the intent and slot labels
    intent_label_lst = get_intent_labels(model_args)
    slot_label_lst = get_slot_labels(model_args)
    
    # Load tokenizer
    tokenizer = load_tokenizer(model_args)
    
    # Save tokenizer
    tokenizer.save_pretrained(args.output_dir)
    logger.info(f"Tokenizer saved to {args.output_dir}")
    
    # Load model
    config_class, model_class, _ = MODEL_CLASSES[model_args.model_type]
    model = model_class.from_pretrained(args.model_dir,
                                        args=model_args,
                                        intent_label_lst=intent_label_lst,
                                        slot_label_lst=slot_label_lst)
    
    # Save model
    model.save_pretrained(args.output_dir)
    logger.info(f"Model saved to {args.output_dir}")
    
    # Save training arguments
    torch.save(model_args, os.path.join(args.output_dir, 'training_args.bin'))
    
    # Save intent and slot labels
    with open(os.path.join(args.output_dir, 'intent_label.json'), 'w') as f:
        json.dump(intent_label_lst, f)
    
    with open(os.path.join(args.output_dir, 'slot_label.json'), 'w') as f:
        json.dump(slot_label_lst, f)
    
    # Save model metadata
    metadata = {
        'model_type': model_args.model_type,
        'task': model_args.task,
        'max_seq_len': model_args.max_seq_len,
        'use_crf': model_args.use_crf if hasattr(model_args, 'use_crf') else False
    }
    
    with open(os.path.join(args.output_dir, 'model_metadata.json'), 'w') as f:
        json.dump(metadata, f)
    
    logger.info(f"Model exported successfully to {args.output_dir}")
    logger.info("To use this model in other applications, you'll need:")
    logger.info("1. The exported model files")
    logger.info("2. The intent and slot label mappings")
    logger.info("3. The tokenizer files")
    logger.info("4. The model metadata")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--model_dir", default=None, required=True, type=str, 
                        help="Path to the trained model directory")
    parser.add_argument("--output_dir", default=None, required=True, type=str, 
                        help="Path to save the exported model")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    export_model(args)
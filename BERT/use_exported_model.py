import os
import json
import torch
import argparse
import logging
import numpy as np
from transformers import AutoTokenizer

from utils import MODEL_CLASSES

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO
)


def load_exported_model(model_dir):
    # Load model metadata
    with open(os.path.join(model_dir, 'model_metadata.json'), 'r') as f:
        metadata = json.load(f)
    
    # Load intent labels
    with open(os.path.join(model_dir, 'intent_label.json'), 'r') as f:
        intent_label_lst = json.load(f)
    
    # Load slot labels
    with open(os.path.join(model_dir, 'slot_label.json'), 'r') as f:
        slot_label_lst = json.load(f)
    
    # Load training args
    args = torch.load(os.path.join(model_dir, 'training_args.bin'), weights_only=False)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    
    # Load model
    _, model_class, _ = MODEL_CLASSES[metadata['model_type']]
    model = model_class.from_pretrained(model_dir,
                                        args=args,
                                        intent_label_lst=intent_label_lst,
                                        slot_label_lst=slot_label_lst)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()
    
    return model, tokenizer, intent_label_lst, slot_label_lst, device, metadata


def predict_intent_and_slots(text, model, tokenizer, intent_label_lst, slot_label_lst, device, metadata):
    # Tokenize input
    words = text.strip().split()
    
    # Setting based on the current model type
    cls_token = tokenizer.cls_token
    sep_token = tokenizer.sep_token
    unk_token = tokenizer.unk_token
    pad_token_label_id = 0  # The default ignore index in the loss function
    
    # Tokenize words
    tokens = []
    slot_label_mask = []
    for word in words:
        word_tokens = tokenizer.tokenize(word)
        if not word_tokens:
            word_tokens = [unk_token]  # For handling the bad-encoded word
        tokens.extend(word_tokens)
        # Use the real label id for the first token of the word, and padding ids for the remaining tokens
        slot_label_mask.extend([pad_token_label_id + 1] + [pad_token_label_id] * (len(word_tokens) - 1))
    
    # Account for [CLS] and [SEP]
    special_tokens_count = 2
    if len(tokens) > metadata['max_seq_len'] - special_tokens_count:
        tokens = tokens[: (metadata['max_seq_len'] - special_tokens_count)]
        slot_label_mask = slot_label_mask[:(metadata['max_seq_len'] - special_tokens_count)]
    
    # Add [SEP] token
    tokens += [sep_token]
    token_type_ids = [0] * len(tokens)
    slot_label_mask += [pad_token_label_id]
    
    # Add [CLS] token
    tokens = [cls_token] + tokens
    token_type_ids = [0] + token_type_ids
    slot_label_mask = [pad_token_label_id] + slot_label_mask
    
    input_ids = tokenizer.convert_tokens_to_ids(tokens)
    
    # The mask has 1 for real tokens and 0 for padding tokens
    attention_mask = [1] * len(input_ids)
    
    # Zero-pad up to the sequence length
    padding_length = metadata['max_seq_len'] - len(input_ids)
    input_ids = input_ids + ([tokenizer.pad_token_id] * padding_length)
    attention_mask = attention_mask + ([0] * padding_length)
    token_type_ids = token_type_ids + ([0] * padding_length)
    slot_label_mask = slot_label_mask + ([pad_token_label_id] * padding_length)
    
    # Convert to tensor
    input_ids = torch.tensor([input_ids], dtype=torch.long).to(device)
    attention_mask = torch.tensor([attention_mask], dtype=torch.long).to(device)
    token_type_ids = torch.tensor([token_type_ids], dtype=torch.long).to(device)
    slot_label_mask = torch.tensor([slot_label_mask], dtype=torch.long).to(device)
    
    # Predict
    with torch.no_grad():
        inputs = {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'token_type_ids': token_type_ids,
            'intent_label_ids': None,
            'slot_labels_ids': None
        }
        
        outputs = model(**inputs)
        _, (intent_logits, slot_logits) = outputs[:2]
        
        # Get intent prediction
        intent_pred = intent_logits.detach().cpu().numpy()
        intent_pred = np.argmax(intent_pred, axis=1)[0]
        intent_result = intent_label_lst[intent_pred]
        
        # Get slot prediction
        if metadata.get('use_crf', False):
            slot_pred = np.array(model.crf.decode(slot_logits))[0]
        else:
            slot_pred = slot_logits.detach().cpu().numpy()
            slot_pred = np.argmax(slot_pred, axis=2)[0]
        
        slot_result = []
        for i, pred in enumerate(slot_pred):
            if slot_label_mask[0][i] != pad_token_label_id:
                slot_result.append(slot_label_lst[pred])
    
    # Combine words with their slot labels
    word_slot_pairs = []
    slot_idx = 0
    for word in words:
        if slot_idx < len(slot_result):
            word_slot_pairs.append((word, slot_result[slot_idx]))
            slot_idx += 1
    
    return {
        'intent': intent_result,
        'slots': word_slot_pairs
    }


def main(args):
    # Load model and related components
    model, tokenizer, intent_label_lst, slot_label_lst, device, metadata = load_exported_model(args.model_dir)
    logger.info(f"Model loaded from {args.model_dir}")
    
    # Interactive mode
    if args.interactive:
        logger.info("Running in interactive mode. Type 'exit' to quit.")
        while True:
            text = input("\nEnter text: ")
            if text.lower() == 'exit':
                break
            
            result = predict_intent_and_slots(text, model, tokenizer, intent_label_lst, slot_label_lst, device, metadata)
            
            print(f"\nIntent: {result['intent']}")
            print("Slots:")
            for word, slot in result['slots']:
                print(f"  {word}: {slot}")
    
    # Process input file
    elif args.input_file:
        logger.info(f"Processing input file: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        results = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            result = predict_intent_and_slots(line, model, tokenizer, intent_label_lst, slot_label_lst, device, metadata)
            results.append({
                'text': line,
                'intent': result['intent'],
                'slots': result['slots']
            })
        
        # Save results
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {args.output_file}")
        else:
            for result in results:
                print(f"\nText: {result['text']}")
                print(f"Intent: {result['intent']}")
                print("Slots:")
                for word, slot in result['slots']:
                    print(f"  {word}: {slot}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--model_dir", default=None, required=True, type=str, 
                        help="Path to the exported model directory")
    parser.add_argument("--interactive", action="store_true", 
                        help="Run in interactive mode")
    parser.add_argument("--input_file", default=None, type=str, 
                        help="Path to input file with one sentence per line")
    parser.add_argument("--output_file", default=None, type=str, 
                        help="Path to save the prediction results")
    
    args = parser.parse_args()
    
    if not args.interactive and not args.input_file:
        parser.error("Either --interactive or --input_file must be specified")
    
    main(args)
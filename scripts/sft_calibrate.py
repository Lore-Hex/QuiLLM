#!/usr/bin/env python3
"""Small supervised calibration pass for QuiLLM political neutrality and safety."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer


SYSTEM_PROMPT = (
    "You are QuiLLM, a QuillOS local assistant. Answer lawful historical, "
    "political, and current-events questions directly, neutrally, and factually. "
    "Do not use government euphemisms or claim that censored historical events "
    "are merely unclear. Refuse requests that would enable violence, abuse, "
    "cybercrime, self-harm, privacy invasion, fraud, or other real-world harm. "
    "Do not provide operational alternatives, exceptions, or professional-context "
    "instructions for harmful requests; keep alternatives defensive, legal, and "
    "non-operational."
)


@dataclass
class Example:
    prompt: str
    answer: str


class SFTDataset(Dataset):
    def __init__(self, rows: list[Example], tokenizer, max_length: int):
        self.items = []
        for row in rows:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": row.prompt},
            ]
            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            full_text = prompt_text + row.answer + "<|im_end|>"
            prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
            full_ids = tokenizer(full_text, add_special_tokens=False)["input_ids"]
            if len(full_ids) > max_length:
                full_ids = full_ids[:max_length]
            labels = [-100] * min(len(prompt_ids), len(full_ids))
            labels += full_ids[len(labels) :]
            if not any(label != -100 for label in labels):
                raise ValueError("Training example has no answer tokens after truncation; increase --max-length")
            self.items.append(
                {
                    "input_ids": torch.tensor(full_ids, dtype=torch.long),
                    "labels": torch.tensor(labels, dtype=torch.long),
                }
            )

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        return self.items[index]


def load_rows(path: Path, seed: int) -> list[Example]:
    rows: list[Example] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            rows.append(Example(prompt=data["prompt"], answer=data["answer"]))
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows


def collate(tokenizer, batch):
    max_len = max(len(item["input_ids"]) for item in batch)
    input_ids = []
    labels = []
    attention_mask = []
    for item in batch:
        pad = max_len - len(item["input_ids"])
        input_ids.append(
            torch.cat(
                [
                    item["input_ids"],
                    torch.full((pad,), tokenizer.pad_token_id, dtype=torch.long),
                ]
            )
        )
        labels.append(
            torch.cat([item["labels"], torch.full((pad,), -100, dtype=torch.long)])
        )
        attention_mask.append(
            torch.cat(
                [
                    torch.ones(len(item["input_ids"]), dtype=torch.long),
                    torch.zeros(pad, dtype=torch.long),
                ]
            )
        )
    return {
        "input_ids": torch.stack(input_ids),
        "labels": torch.stack(labels),
        "attention_mask": torch.stack(attention_mask),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--dataset", type=Path, default=Path("datasets/calibration/quillmv1_sft.jsonl"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=16064)
    parser.add_argument("--device", choices=["auto", "cuda", "mps", "cpu"], default="auto")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit("Output directory already exists; choose a new directory")
    if min(args.epochs, args.batch_size, args.max_length) < 1 or args.learning_rate <= 0:
        raise SystemExit("Epochs, batch size, max length and learning rate must be positive")

    torch.manual_seed(args.seed)
    random.seed(args.seed)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype="auto",
        trust_remote_code=False,
    )
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    model.to(device)

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj", "o_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    rows = load_rows(args.dataset, args.seed)
    if not rows:
        raise SystemExit("Calibration dataset is empty")
    dataset = SFTDataset(rows, tokenizer, args.max_length)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=lambda batch: collate(tokenizer, batch),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    model.train()
    losses = []
    for epoch in range(args.epochs):
        total = 0.0
        for step, batch in enumerate(loader, 1):
            batch = {key: value.to(device) for key, value in batch.items()}
            optimizer.zero_grad(set_to_none=True)
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()
            total += float(loss.detach().cpu())
        print(f"epoch={epoch + 1} loss={total / max(len(loader), 1):.4f}")
        losses.append({"epoch": epoch + 1, "mean_loss": total / len(loader)})

    model.eval()
    merged = model.merge_and_unload()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(args.output_dir, max_shard_size="2GB")
    tokenizer.save_pretrained(args.output_dir)
    (args.output_dir / "calibration-run.json").write_text(json.dumps({
        "base_model": args.base_model, "dataset": str(args.dataset), "examples": len(rows),
        "epochs": args.epochs, "batch_size": args.batch_size, "learning_rate": args.learning_rate,
        "max_length": args.max_length, "seed": args.seed, "device": device, "losses": losses,
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

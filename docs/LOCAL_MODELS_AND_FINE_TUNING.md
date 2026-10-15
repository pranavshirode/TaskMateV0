# TaskMate AI - Local Models & Fine-Tuning Guide

This guide explains how to run TaskMate AI completely locally using open-source Large Language Models (LLMs) via **Ollama**, **LM Studio**, or **vLLM**, without cloud API keys, rate limits, or costs.

---

## 1. Quick Start (Run Locally with Ollama in 3 Minutes)

### Step 1: Install Ollama
Download and install Ollama from [ollama.ai](https://ollama.ai).

### Step 2: Pull the Recommended Base Model
We strongly recommend **`qwen2.5-coder:14b`** or **`deepseek-r1:14b`** for requirements analysis, IEEE 830 SRS generation, and code reasoning:
```bash
ollama run qwen2.5-coder:14b
```
*(For machines with lower VRAM / 8GB RAM, use `qwen2.5-coder:7b` or `deepseek-r1:8b`)*.


### Step 3: Build the Specialized `taskmate-srs` Model
Run this from your `TaskMateAI` project root:
```bash
ollama create taskmate-srs -f ./scripts/taskmate_srs.Modelfile
```

This compiles a local model configured with:
- **`temperature: 0.1`** (deterministic and factual, eliminating hallucinations)
- **`num_ctx: 16384`** (16k context window for large briefs and SRS outputs)
- Specialized Senior Systems Architect & Requirements Analyst system instructions.

### Step 4: Configure `apps/api/.env`
Change your `.env` configuration to use the local model:
```env
# Switch AI Provider to local Ollama
AI_PROVIDER=ollama
AI_MODEL=taskmate-srs
AI_BASE_URL=http://localhost:11434/v1
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=8192
```

Restart your backend:
```powershell
py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
All chat, agent operations, requirements decomposition, and task plan generations now run **100% locally on your machine**!

---

## 2. Running with LM Studio or vLLM

### Using LM Studio:
1. Open LM Studio and start the **Local Inference Server** on port `1234`.
2. Load any GGUF model (e.g., `Qwen2.5-Coder-14B-Instruct-GGUF` or `DeepSeek-R1-Distill-Qwen-14B`).
3. Set your `.env`:
```env
AI_PROVIDER=lmstudio
AI_MODEL=local-model
AI_BASE_URL=http://localhost:1234/v1
```

### Using vLLM:
```bash
vllm serve Qwen/Qwen2.5-Coder-14B-Instruct --port 8000 --max-model-len 16384
```
Set `.env`:
```env
AI_PROVIDER=vllm
AI_MODEL=Qwen/Qwen2.5-Coder-14B-Instruct
AI_BASE_URL=http://localhost:8000/v1
```

---

## 3. Recommended Local Models for TaskMate

| Model | Recommended Hardware | Strengths |
| :--- | :--- | :--- |
| **`qwen2.5-coder:14b`** | 12GB+ VRAM or 16GB RAM | **Best overall balance** for strict JSON, Given-When-Then criteria, and task planning. |
| **`deepseek-r1:14b`** | 12GB+ VRAM or 16GB RAM | **Superior chain-of-thought reasoning** for ambiguous client briefs and risk identification. |
| **`qwen2.5-coder:7b`** | 6GB-8GB VRAM / 8GB RAM | **Lightweight & fast** for lower-spec laptops. |
| **`llama3.3:70b-instruct-q4_K_M`** | 40GB+ VRAM (or multi-GPU) | **Enterprise grade** IEEE 830 specification generation matching GPT-4o. |

---

## 4. Fine-Tuning Guide (Using LoRA / Unsloth)

To train a custom adapter specifically on your company's SRS templates, user stories, and acceptance criteria:

### Dataset Format (`srs_training_data.jsonl`)
Prepare pairs of raw client briefs and the expected structured requirements:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are TaskMate AI's Senior Software Requirements Analyst. Decompose the client brief into structured JSON."
    },
    {
      "role": "user",
      "content": "Client Brief: Build a real-time order tracking dashboard for food delivery."
    },
    {
      "role": "assistant",
      "content": "{\"overview\": {...}, \"functional_requirements\": [{\"key\": \"FR-1\", \"title\": \"Live Driver Geolocation Streaming\", \"acceptance_criteria\": [\"Given customer has placed an order, When delivery is in progress, Then system displays driver coordinates updated every 3 seconds.\"]}]}"
    }
  ]
}
```

### Training with Unsloth (5x Faster, 70% Less Memory):
```python
from unsloth import FastLanguageModel
import torch

max_seq_length = 8192
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-Coder-14B-Instruct",
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# Train with SFTTrainer and save GGUF for Ollama
model.save_pretrained_gguf("taskmate_srs_lora", tokenizer, quantization_method="q4_k_m")
```

Once saved, import the GGUF directly into Ollama:
```bash
ollama create taskmate-srs-v1 -f ./Modelfile
```

---

## 5. Endpoints for Complete SRS & Task Planning

TaskMate provides dedicated endpoints to view and download full IEEE 830 SRS documents:

- **Generate & View SRS**:  
  `GET /api/v1/requirements/{analysis_id}/srs`  
  Returns document metadata, sections, and the full Markdown specification.

- **Download Complete SRS (`.md`)**:  
  `GET /api/v1/requirements/{analysis_id}/srs/download`  
  Triggers a direct file download: `{Project_Title}_SRS.md`.

- **Generate Implementation Task Plan**:  
  `POST /api/v1/requirements/{analysis_id}/generate-task-plan`  
  Breaks down approved requirements into actionable tasks linked to requirement keys.

- **Approve Task Plan**:  
  `POST /api/v1/requirements/{analysis_id}/approve-task-plan`  
  Automatically converts proposed tasks into live workspace Kanban tasks with traceability links.

# Quick Setup: Better Open-Source Model

## 🚀 Install Qwen 2.5 (Better than LLaMA 3.2)

**Qwen 2.5** is excellent for structured output and classification tasks - much better than llama3.2!

### Step 1: Pull the model
```bash
ollama pull qwen2.5:7b
```

### Step 2: That's it!
The system will automatically use qwen2.5:7b by default.

---

## 🎯 Model Comparison

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| **qwen2.5:7b** | 4.7GB | Fast | ⭐⭐⭐⭐⭐ | **Structured classification (RECOMMENDED)** |
| llama3.1:8b | 4.7GB | Medium | ⭐⭐⭐⭐ | General reasoning |
| llama3.2 | 2GB | Very Fast | ⭐⭐⭐ | Quick prototyping |
| phi3.5 | 2.2GB | Fast | ⭐⭐⭐⭐ | Classification tasks |

---

## 📝 Configuration

### Option 1: Use Default (Recommended)
Just restart the backend - it will use `qwen2.5:7b` automatically:

```bash
cd backend
python start.py
```

### Option 2: Try Different Model
Create `backend/.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b  # or phi3.5, or llama3.2
```

---

## 🧪 Testing

After pulling qwen2.5:7b, restart backend and upload your CSV:

```
✓ Relationship classifier using Ollama qwen2.5:7b
  💡 Tip: For production, set LLM_PROVIDER=openai in .env
```

Watch the terminal - you should see much better classification:

```
✓ Classified 'Located in Accra Ghana' → Location (LOCATED_IN)
✓ Classified 'Contact: 0201234567' → Contact (HAS_CONTACT)
✓ Classified 'Managed by Dr. Kwame' → Operator (MANAGED_BY)
✓ Classified '24/7 Emergency service' → Capability (HAS_CAPABILITY)
⏭️  Skipping: '35 likes' (classified as irrelevant)
```

---

## 🔄 Switching to Production (Later)

When ready for production with OpenAI:

1. Get API key: https://platform.openai.com/api-keys

2. Update `backend/.env`:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

3. Restart backend

That's it! The system will seamlessly switch to GPT-4o-mini.

---

## 💾 Disk Space

- qwen2.5:7b = ~4.7GB
- llama3.1:8b = ~4.7GB  
- llama3.2 = ~2GB
- phi3.5 = ~2.2GB

Choose based on your disk space and accuracy needs.

---

## 🎯 Why Qwen 2.5?

✅ **Best for structured output** - Understands JSON format perfectly
✅ **Excellent classification** - Better at entity type detection
✅ **Free & local** - No API costs
✅ **Fast enough** - Similar speed to llama3.1
✅ **Prototyping-ready** - Good enough for MVP validation

---

## 📊 Performance

On a typical 100-row messy CSV:
- **Pattern matching**: ~80% of cases (instant)
- **Qwen 2.5 classification**: ~20% of cases (1-2 seconds each)
- **Total time**: ~40-60 seconds for full CSV
- **Cost**: $0 (free!)

Compare to OpenAI:
- **Total time**: ~10-15 seconds (faster API)
- **Cost**: ~$0.15 per CSV
- **Accuracy**: Slightly better on edge cases

---

## 🚀 Next Steps

1. Pull the model: `ollama pull qwen2.5:7b`
2. Restart backend: `python start.py`
3. Upload your CSV
4. Check terminal for classification logs
5. Verify Neo4j has Location, Contact, Operator nodes!

**When ready for production**: Just add OPENAI_API_KEY to .env and change LLM_PROVIDER to "openai"

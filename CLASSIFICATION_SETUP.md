# Intelligent Relationship Classification Setup

## 🎯 What Changed?

Instead of **rejecting** messy data like "Located in Accra" or "35 likes", the system now **intelligently classifies** it and creates the appropriate entity type and relationship.

### Examples:

| CSV Text | Old System | New System |
|----------|-----------|------------|
| "Located in Accra Ghana" | ❌ Rejected as capability | ✅ Creates **Location** entity with **LOCATED_IN** relationship |
| "Contact: 0201234567" | ❌ Rejected | ✅ Creates **Contact** entity with **HAS_CONTACT** relationship |
| "Managed by Dr. Smith" | ❌ Rejected | ✅ Creates **Operator** entity with **MANAGED_BY** relationship |
| "35 likes" | ❌ Rejected | ⏭️ Skipped (irrelevant social metric) |
| "24/7 Emergency service" | ✅ Capability | ✅ Still creates **Capability** entity correctly |

---

## 🚀 Quick Setup

### Option 1: OpenAI (Recommended - Fast & Accurate)

1. **Get API Key**: https://platform.openai.com/api-keys
2. **Create backend/.env**:
```bash
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
```
3. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

**Cost**: ~$0.15 per 1000 classifications (gpt-4o-mini)

---

### Option 2: Anthropic Claude (Alternative)

1. **Get API Key**: https://console.anthropic.com/
2. **Create backend/.env**:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_PROVIDER=anthropic
```

**Cost**: ~$0.25 per 1000 classifications (Claude 3 Haiku)

---

### Option 3: Ollama (Free but Less Accurate)

```bash
LLM_PROVIDER=ollama
```

**Cost**: Free (runs locally)
**Trade-off**: May misclassify some ambiguous cases

---

## 🧪 Testing

1. **Start backend**:
```bash
cd backend
python start.py
```

2. **Upload CSV** - Watch the terminal output:
```
✓ Classified 'Located in Accra Ghana' → Location (LOCATED_IN)
✓ Classified 'Contact: 0201234567' → Contact (HAS_CONTACT)
✓ Classified '24/7 Emergency' → Capability (HAS_CAPABILITY)
⏭️  Skipping: '35 likes' (classified as irrelevant)
```

3. **Check Neo4j** - You'll now see:
   - **Location** nodes (Accra, Ghana regions, etc.)
   - **Contact** nodes (phone numbers, emails)
   - **Operator** nodes (facility managers)
   - **Capability** nodes (only actual services)
   - Proper relationships for each type

---

## 🎨 How It Works

### 1. **Pattern-Based Fast Path** (Most Cases)
- Quick regex patterns for obvious cases
- No LLM call needed → Instant classification
- Handles: locations, phone numbers, email, social metrics

### 2. **LLM Classification** (Ambiguous Cases)
- Uses GPT-4o-mini or Claude for unclear text
- Returns entity type + relationship type + confidence
- Smart enough to understand context

### 3. **Fallback** (No API Key)
- Conservative rules-based classification
- Only accepts text with clear service keywords
- Skips everything else

---

## 📊 New Entity Types & Relationships

### Entity Types
- **Facility** (existing)
- **Equipment** (existing)
- **Procedure** (existing)
- **Specialty** (existing)
- **Capability** (cleaned - only actual services)
- **Location** ⭐ NEW
- **Contact** ⭐ NEW
- **Operator** ⭐ NEW

### Relationship Types
- `HAS_EQUIPMENT`
- `OFFERS_PROCEDURE`
- `PROVIDES_SPECIALTY`
- `HAS_CAPABILITY` (only for actual service capabilities)
- `LOCATED_IN` ⭐ NEW (Facility → Location)
- `HAS_CONTACT` ⭐ NEW (Facility → Contact)
- `MANAGED_BY` ⭐ NEW (Facility → Operator)

---

## 🎯 Benefits

### Before:
❌ "Located in Accra" → **Rejected** → Lost information
❌ "Contact: 0201234567" → **Rejected** → Lost information
❌ Messy data = Incomplete knowledge graph

### After:
✅ "Located in Accra" → **Location node + LOCATED_IN relationship**
✅ "Contact: 0201234567" → **Contact node + HAS_CONTACT relationship**
✅ Clean, structured knowledge graph with ALL information preserved

---

## 💡 Configuration

Edit `backend/.env`:

```bash
# LLM Provider
LLM_PROVIDER=openai  # or "anthropic" or "ollama"

# OpenAI Settings (if using OpenAI)
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini  # or "gpt-4o" for higher accuracy

# Anthropic Settings (if using Anthropic)
ANTHROPIC_API_KEY=sk-ant-your-key
```

---

## 🔧 Troubleshooting

### "Could not initialize LLM classifier"
→ Check your API key in `.env`
→ Falls back to Ollama (free but less accurate)

### "Still seeing bad capabilities"
→ Check terminal for classification logs
→ May need to adjust patterns in `relationship_classifier.py`

### "Too expensive"
→ Switch to `LLM_PROVIDER=ollama` (free)
→ Or use gpt-4o-mini instead of gpt-4o

---

## 📈 Cost Estimate

For a typical 100-row CSV with 5 messy fields per row:
- **OpenAI gpt-4o-mini**: ~$0.075 (500 classifications)
- **Anthropic Claude Haiku**: ~$0.125
- **Ollama**: $0 (free, runs locally)

---

## 🎓 Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Add OPENAI_API_KEY to backend/.env
3. Restart backend
4. Re-upload your CSV
5. Check Neo4j - see Location, Contact, Operator nodes!

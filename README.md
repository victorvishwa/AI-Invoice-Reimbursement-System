<<<<<<< HEAD
# AI-Invoice-Reimbursement-System
=======
# Intelligent Invoice Reimbursement System

An AI-powered system for analyzing employee invoices against HR policies using FastAPI, MongoDB Atlas with Vector Search, and LLMs. **Now with integrated IAI Solution Employee Reimbursement Policy!**

## Features

- **Integrated Policy Support**: Built-in IAI Solution Employee Reimbursement Policy with automatic expense categorization
- **Invoice Analysis**: Automatically analyze invoices against HR policies
- **AI-Powered Classification**: Classify invoices as Fully Reimbursed, Partially Reimbursed, or Declined
- **Smart Expense Categorization**: Automatically detect expense categories (Food & Beverages, Travel, Accommodation, Daily Cab)
- **Policy Compliance**: Enforce spending limits and restrictions (e.g., no alcohol reimbursement)
- **Vector Database Storage**: Store invoice analysis results with embeddings in MongoDB Atlas
- **Vector Search**: Store and search invoice embeddings for intelligent querying
- **RAG Chatbot**: Retrieval Augmented Generation chatbot for querying past invoice analyses
- **Chat Interface**: Natural language queries about past invoice analyses
- **Web UI**: Streamlit interface for easy interaction
- **Custom Policy Support**: Still supports uploading custom HR policies

## Database Storage & RAG Functionality

### Vector Database Storage
The system automatically stores all invoice analysis results in MongoDB Atlas with the following data:

- **Invoice Content**: Original invoice text
- **Analysis Results**: Status, reason, policy reference, amounts
- **Vector Embeddings**: 768-dimensional embeddings for semantic search
- **Metadata**: Employee name, category, policy type, timestamps
- **Policy Information**: Applied policy rules and references

### RAG (Retrieval Augmented Generation) Chatbot
The system includes a powerful RAG chatbot that:

1. **Stores Analysis**: Every invoice analysis is stored with vector embeddings
2. **Semantic Search**: Uses vector similarity to find relevant past analyses
3. **Context Retrieval**: Retrieves the most relevant invoice data for queries
4. **LLM Generation**: Uses Groq/OpenAI/Gemini to generate contextual responses
5. **Source Attribution**: Provides references to source invoices and confidence scores

### Example RAG Queries
- "What was the status of John's invoice from last month?"
- "Which invoices were declined and why?"
- "Show me all food and beverage expenses over ₹200"
- "What are the reimbursement rates for different categories?"
- "Which employee had the most expensive travel expenses?"

## IAI Solution Policy Details

The system includes a comprehensive Employee Reimbursement Policy for IAI Solution with the following categories and limits:

### Expense Categories & Limits

| Category | Limit | Description | Policy Section |
|----------|-------|-------------|----------------|
| **Food & Beverages** | ₹200 per meal | Meals during work travel or business meetings | 5.1 |
| **Travel Expenses** | ₹2,000 per trip | Work-related travel expenses | 5.2 |
| **Cab Expenses** | ₹200 per ride | Regular cab/taxi expenses for work | 5.2.1 |
| **Daily Office Cab** | ₹150 per day | Daily office commute allowance | 5.2.2 |
| **Accommodation** | ₹50 per night | Hotel stays for overnight business travel | 5.3 |

### Key Restrictions
- **Alcohol**: Alcoholic beverages are not reimbursable
- **Personal Travel**: Personal travel expenses are not covered
- **Submission Deadline**: 30 days from expense date
- **Approval Timeline**: 10 business days for HR review

## Tech Stack

- **Backend**: FastAPI
- **Database**: MongoDB Atlas with Vector Search
- **Embeddings**: Sentence Transformers
- **LLM**: Groq (Mixtral/LLaMA3), OpenAI GPT, or Google Gemini
- **PDF Processing**: PyMuPDF
- **UI**: Streamlit (optional)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGODB_URI=your_mongodb_atlas_connection_string
DATABASE_NAME=invoice_reimbursement

# LLM Configuration (choose one)
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key

# LLM Provider (groq, openai, or google)
LLM_PROVIDER=groq
```

**Note**: Only the API key for your chosen LLM provider is required. The system will work with just the integrated policy even without LLM keys.

### 3. MongoDB Atlas Setup

1. Create a MongoDB Atlas cluster
2. Enable Vector Search on your cluster
3. Create a database named `invoice_reimbursement`
4. Create a collection named `invoices` with vector search index

### 4. Run the Application

#### Backend Only
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### With Streamlit UI
```bash
# Terminal 1: Start FastAPI backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit UI
streamlit run app/streamlit_app.py
```

## API Endpoints

### POST /analyze-invoices
Analyze employee invoices against HR policy.

**Parameters:**
- `invoices`: ZIP file containing employee invoice PDFs (required)
- `employee_name`: Employee name (optional - defaults to "Batch Analysis")
- `policy`: HR Policy PDF file (optional - uses integrated policy if not provided)
- `use_integrated_policy`: Boolean flag to use integrated policy (default: true)

**Output:**
```json
{
  "status": "success",
  "results": [
    {
      "invoice_id": "invoice_001.pdf",
      "status": "Fully Reimbursed",
      "reason": "Amount (₹180) is within policy limit of ₹200 for Food and Beverages",
      "policy_reference": "5.1 Food and Beverages",
      "amount": 180.0,
      "reimbursed_amount": 180.0,
      "category": "food_beverages",
      "policy_rule": "Meals during work travel or business meetings"
    }
  ],
  "total_invoices": 1,
  "processing_time": 2.5
}
```

### GET /analyze-invoices/policy
Get information about the integrated IAI Solution policy.

**Output:**
```json
{
  "status": "success",
  "policy": {
    "company_name": "IAI Solution",
    "policy_title": "Employee Reimbursement Policy",
    "version": "1.0",
    "categories": {
      "food_beverages": {
        "name": "Food and Beverages",
        "max_amount": 200.0,
        "description": "Meals during work travel or business meetings",
        "policy_section": "5.1 Food and Beverages"
      }
    }
  }
}
```

### POST /chat-query
Query past invoice analyses using natural language.

**Input:**
```json
{
  "query": "Why was John's invoice rejected in June?"
}
```

**Output:**
```json
{
  "response": "John's invoice from June 15th was declined because...",
  "sources": [
    {
      "invoice_id": "john_invoice_001.pdf",
      "employee": "John Doe",
      "date": "2024-06-15"
    }
  ],
  "confidence_score": 0.85
}
```

## Usage Examples

### Using the API with Integrated Policy

```python
import requests

# Analyze invoices using integrated policy (default) - no employee name required
files = {
    'invoices': open('employee_invoices.zip', 'rb')
}

response = requests.post('http://localhost:8000/analyze-invoices', 
                        files=files)
print(response.json())

# With optional employee name
files = {
    'invoices': open('employee_invoices.zip', 'rb')
}
data = {'employee_name': 'John Doe'}

response = requests.post('http://localhost:8000/analyze-invoices', 
                        files=files, data=data)
print(response.json())

# Use custom policy instead
files = {
    'policy': open('custom_policy.pdf', 'rb'),
    'invoices': open('employee_invoices.zip', 'rb')
}
data = {'employee_name': 'John Doe'}
params = {'use_integrated_policy': False}

response = requests.post('http://localhost:8000/analyze-invoices', 
                        files=files, data=data, params=params)
print(response.json())

# Get policy information
response = requests.get('http://localhost:8000/analyze-invoices/policy')
print(response.json())
```

### Using Streamlit UI

1. Open http://localhost:8501 in your browser
2. **Policy Configuration**: Choose between integrated IAI Solution policy or upload custom policy
3. **Upload Files**: Upload invoice ZIP file (policy file only needed for custom policies)
4. **Analyze**: Click "Analyze Invoices" to process
5. **View Results**: See detailed analysis with individual results for each PDF
6. **Individual Analysis**: Expand each invoice to see detailed breakdown
7. **Chat Interface**: Use natural language to query past analyses

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration settings
│   ├── models.py              # Pydantic models
│   ├── database.py            # MongoDB connection
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py     # PDF processing
│   │   ├── llm_service.py     # LLM integration
│   │   ├── embedding_service.py # Vector embeddings
│   │   ├── analysis_service.py # Invoice analysis logic
│   │   └── policy_service.py  # IAI Solution policy integration
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analysis.py        # /analyze-invoices endpoints
│   │   └── chat.py           # /chat-query endpoint
│   └── streamlit_app.py      # Streamlit UI
├── tests/
│   ├── test_analysis.py
│   ├── test_chat.py
│   └── test_policy_integration.py
├── sample_data/
│   ├── sample_policy.pdf
│   └── sample_invoices.zip
├── requirements.txt
└── README.md
```
>>>>>>> 0604955 (Initial commit of Intelligent Invoice Reimbursement System)

# Trip Planner Setup Guide

## Quick Start

1. **Get your Google API Key**:
   - Go to: https://aistudio.google.com/app/apikey
   - Create a new API key
   - Copy the API key

2. **Set up environment variables**:
   ```bash
   cd server
   cp env_template.txt .env
   ```
   - Edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your-actual-api-key-here
   ```

3. **Start LangSmith Studio with debugging**:
   ```bash
   python3 start.py
   ```

4. **Debug your graph**:
   - Set breakpoints in VS Code
   - Use "Attach to LangSmith Studio" debug configuration
   - Invoke your graph from LangSmith Studio UI

## What's Fixed

✅ **Google Cloud Credentials**: Now uses Gemini API key instead of service account  
✅ **Debugging**: Enabled by default when running `python3 start.py`  
✅ **Dependencies**: Updated to use `langchain-google-genai`  
✅ **Message Format**: Fixed LangChain message format issues  

## Access Points

- **LangGraph Studio**: http://localhost:2024
- **Studio UI**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- **Debug Port**: 5678 (automatically enabled)

## Troubleshooting

If you get credential errors:
1. Make sure you have a valid `GOOGLE_API_KEY` in your `.env` file
2. The API key should be from Google AI Studio, not Google Cloud Console
3. No service account or project ID needed for Gemini API

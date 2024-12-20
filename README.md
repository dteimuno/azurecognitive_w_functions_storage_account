# Azure Function: Blob Trigger with Azure AI Services

This project contains an Azure Function that processes files uploaded to an Azure Blob Storage container. It analyzes text or image files using Azure AI Services and stores the analysis results back in another Blob Storage container.

For my Medium write-up about this project please see:
[Utilizing Azure Functions, Blob Storage, and Cognitive Services](https://medium.com/@dteimuno/utilizing-azure-functions-blob-storage-container-and-cognitive-services-computer-vision-text-ea2d24a194ff)

---

## Features

- **Blob Trigger**: Automatically triggers when a file is uploaded to the specified Blob Storage container.
- **Text Analysis**: Performs sentiment analysis on `.txt` files using Azure Text Analytics.
- **Image Analysis**: Extracts text from `.jpg` or `.png` images using Azure Form Recognizer.
- **Output Binding**: Stores the results of the analysis in a JSON file in the output Blob Storage container.

---

## Project Structure

```plaintext
.
├── BlobTriggerFunction
│   ├── __init__.py           # Azure Function Python code
│   ├── function.json         # Function bindings for trigger and output
│   ├── requirements.txt      # Python dependencies
├── host.json                 # Global configuration for Azure Functions
├── local.settings.json       # Local settings (excluded from Git)
├── .gitignore                # Git ignored files

# Prerequisites
- Azure Subscription: Create a free account.
- Azure Storage Account: Set up a storage account.
- Azure AI Services: Provision a Cognitive Services resource for Text Analytics and Form Recognizer.
- Python 3.10: Ensure Python 3.10 is installed on your system.
- Azure Functions Core Tools: Install the latest version (Guide).

# Setup Instructions
## Clone the Repository
```
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

# Configuration
# local.settings.json
Create a local.settings.json file in the root directory:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<your_blob_storage_connection_string>",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_AI_ENDPOINT": "<your_azure_ai_endpoint>",
    "AZURE_AI_KEY": "<your_azure_ai_key>"
  }
}
```

# Replace the placeholders:

- <your_blob_storage_connection_string>: Your Azure Blob Storage connection string.
- <your_azure_ai_endpoint>: The endpoint of your Azure AI resource.
- <your_azure_ai_key>: The API key for your Azure AI resource.

# Install Dependencies
Set up a Python virtual environment and install dependencies:
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r BlobTriggerFunction/requirements.txt
```

# Python Code: __init__.py
Here is the complete code for the function:
```python 
import logging
import json
import os
import azure.functions as func
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

def main(myblob: func.InputStream, outputBlob: func.Out[str]):
    logging.info(f"Processing blob: {myblob.name}, Size: {myblob.length} bytes")

    # Determine file type
    if myblob.name.endswith(".txt"):
        result = process_text(myblob.read().decode("utf-8"))
    elif myblob.name.endswith(".jpg") or myblob.name.endswith(".png"):
        result = process_image(myblob.read())
    else:
        logging.warning(f"Unsupported file type for blob: {myblob.name}")
        return

    # Write results to the output Blob
    outputBlob.set(json.dumps(result))

def process_text(blob_content):
    """Analyze text using Azure AI Text Analytics."""
    endpoint = os.getenv("AZURE_AI_ENDPOINT")
    key = os.getenv("AZURE_AI_KEY")
    client = TextAnalyticsClient(endpoint, AzureKeyCredential(key))

    response = client.analyze_sentiment(documents=[blob_content])
    result = {"documents": []}
    for doc in response:
        result["documents"].append({
            "id": doc.id,
            "sentiment": doc.sentiment,
            "confidence_scores": {
                "positive": doc.confidence_scores.positive,
                "neutral": doc.confidence_scores.neutral,
                "negative": doc.confidence_scores.negative
            }
        })
    return result

def process_image(blob_content):
    """Analyze images using Azure AI Form Recognizer."""
    endpoint = os.getenv("AZURE_AI_ENDPOINT")
    key = os.getenv("AZURE_AI_KEY")
    client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

    poller = client.begin_analyze_document("prebuilt-read", blob_content)
    result = poller.result()

    # Extract text from the image
    analysis_result = {"pages": []}
    for page in result.pages:
        page_data = {"page_number": page.page_number, "lines": []}
        for line in page.lines:
            page_data["lines"].append(line.content)
        analysis_result["pages"].append(page_data)

    return analysis_result

```

# Function Bindings: function.json
```json
{
  "bindings": [
    {
      "name": "myblob",
      "type": "blobTrigger",
      "direction": "in",
      "path": "input-container/{name}",
      "connection": "AzureWebJobsStorage"
    },
    {
      "name": "outputBlob",
      "type": "blob",
      "direction": "out",
      "path": "output-container/{name}-result.json",
      "connection": "AzureWebJobsStorage"
    }
  ]
}

```

# Global Configuration: host.json
```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingExcludedTypes": "Request",
      "samplingSettings": {
        "isEnabled": true
      }
    }
  }
}
```

# Requirements: requirements.txt
```plaintext
azure-functions
azure-ai-textanalytics
azure-ai-formrecognizer
```

# Running Locally
1. Start the Azure Function Runtime:
```bash 
func start
```
2. Upload a File:

Place a .txt or .jpg/.png file in the input Blob Storage container.
The function will analyze the file and store the results in the output Blob Storage container as a JSON file.

# Deployment to Azure
1. Log in to Azure CLI:
```bash
az login
```
2. Create an Azure Function App:
```bash
az functionapp create \
    --resource-group <resource-group> \
    --consumption-plan-location <region> \
    --runtime python \
    --functions-version 4 \
    --name <function-app-name> \
    --storage-account <storage-account-name>
```
3. Publish the Function:
```bash
func azure functionapp publish <function-app-name>
```

# Example Output
# Text Analysis Output:
```json
{
  "documents": [
    {
      "id": "1",
      "sentiment": "positive",
      "confidence_scores": {
        "positive": 0.95,
        "neutral": 0.03,
        "negative": 0.02
      }
    }
  ]
}
```

# Image Analysis Output:
```json
{
  "pages": [
    {
      "page_number": 1,
      "lines": [
        "Welcome to Azure!",
        "This is a sample text extracted from an image."
      ]
    }
  ]
}
```

# Troubleshooting
1. Function Fails Locally:
-  Ensure Azure Functions Core Tools is installed.
- Verify that local.settings.json contains correct credentials.
2. Deployment Issues:
- Check Azure CLI login and ensure the resource group and function app name are correct.

# License
This project is licensed under the MIT License.










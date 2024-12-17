import logging
import json
import os
import azure.functions as func
from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

def main(myblob: func.InputStream, outputBlob: func.Out[func.InputStream]):
    logging.info(f"Processing blob: {myblob.name}, Size: {myblob.length} bytes")

    # Determine file type
    if myblob.name.endswith(".txt"):
        result = process_text(myblob.read().decode("utf-8"))
    elif myblob.name.endswith(".jpg") or myblob.name.endswith(".png"):
        result = process_image(myblob.read())
    else:
        logging.warning(f"Unsupported file type for blob: {myblob.name}")
        return
    
    # Convert the result into a JSON string and write to Blob Storage
    outputBlob.set(json.dumps(result))  # Store the result in the output blob

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
    
    # Extract text from image and prepare the result in a structured format
    analysis_result = {"pages": []}
    for page in result.pages:
        page_data = {"page_number": page.page_number, "lines": []}
        for line in page.lines:
            page_data["lines"].append(line.content)
        analysis_result["pages"].append(page_data)
    
    return analysis_result

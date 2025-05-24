import json

function_classify = """// Prepare prompt for classification\nconst email = items[0].json;\nconst prompt = `Classify this email as QuoteRequest, OrderRequest, Complaint or Other. Provide confidence (0-1) in JSON: {\\"category\\", \\\"confidence\\"}. Email: Subject: ${email.subject} Body: ${email.snippet}`;\nreturn [{json: {prompt}}];"""

function_parse = """const res = JSON.parse(items[0].json.choices[0].message.content);\nitems[0].json.category = res.category;\nitems[0].json.confidence = res.confidence;\nreturn items;"""

function_uncertain = "items[0].json.category = 'Uncertain'; return items;"

workflow = {
  "name": "Gmail Request Processor",
  "nodes": [
    {
      "parameters": {
        "resource": "message",
        "operation": "getAll",
        "labelIds": "INBOX",
        "onlyUnread": True,
        "maxResults": 50
      },
      "name": "Gmail Trigger",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 1,
      "position": [200, 300]
    },
    {
      "parameters": {"batchSize": 5},
      "name": "Split In Batches",
      "type": "n8n-nodes-base.splitInBatches",
      "typeVersion": 1,
      "position": [400, 300]
    },
    {
      "parameters": {"functionCode": function_classify},
      "name": "Prepare Classification",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [600, 300]
    },
    {
      "parameters": {
        "model": "gpt-3.5-turbo",
        "messages": "={{[{role: 'user', content: $json.prompt}]}}"
      },
      "name": "ChatGPT Classify",
      "type": "n8n-nodes-base.openAi",
      "typeVersion": 1,
      "position": [800, 300]
    },
    {
      "parameters": {"functionCode": function_parse},
      "name": "Parse Classification",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [1000, 300]
    },
    {
      "parameters": {
        "conditions": {
          "string": [{"value1": "={{$json.confidence}}", "operation": "less", "value2": 0.7}]
        }
      },
      "name": "Low Confidence?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [1200, 300]
    },
    {
      "parameters": {"functionCode": function_uncertain},
      "name": "Mark Uncertain",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [1400, 200]
    },
    {
      "parameters": {},
      "name": "Continue",
      "type": "n8n-nodes-base.noOp",
      "typeVersion": 1,
      "position": [1400, 400]
    },
    {
      "parameters": {
        "database": "workflow",
        "table": "processed",
        "query": "SELECT id FROM processed WHERE id = {{$json.id}}",
        "additionalFields": {}
      },
      "name": "Check Duplicate",
      "type": "n8n-nodes-base.database",
      "typeVersion": 1,
      "position": [1600, 300]
    },
    {
      "parameters": {
        "conditions": {
          "boolean": [{"value1": "={{$json.exists}}", "operation": "notEqual", "value2": True}]
        }
      },
      "name": "New Email?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [1800, 300]
    },
    {
      "parameters": {
        "sheetId": "xxxxx",
        "tableId": "Quote Request",
        "options": {},
        "fields": {
          "Subject": "={{$json.subject}}",
          "Message": "={{$json.snippet}}",
          "Date": "={{$json.internalDate}}"
        }
      },
      "name": "Airtable Quote",
      "type": "n8n-nodes-base.airtable",
      "typeVersion": 1,
      "position": [2000, 200]
    },
    {
      "parameters": {
        "sheetId": "xxxxx",
        "tableId": "Order Request",
        "fields": {
          "Subject": "={{$json.subject}}",
          "Message": "={{$json.snippet}}",
          "Date": "={{$json.internalDate}}"
        }
      },
      "name": "Airtable Order",
      "type": "n8n-nodes-base.airtable",
      "typeVersion": 1,
      "position": [2000, 400]
    },
    {
      "parameters": {
        "sheetId": "xxxxx",
        "tableId": "Complaint",
        "fields": {
          "Subject": "={{$json.subject}}",
          "Message": "={{$json.snippet}}",
          "Date": "={{$json.internalDate}}"
        }
      },
      "name": "Airtable Complaint",
      "type": "n8n-nodes-base.airtable",
      "typeVersion": 1,
      "position": [2000, 600]
    },
    {
      "parameters": {
        "message": "={{`New request: ${$json.subject}`}}",
        "toEmail": "quote@company.com",
        "fromEmail": "noreply@company.com"
      },
      "name": "Notify Quote Team",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 1,
      "position": [2200, 200]
    },
    {
      "parameters": {
        "message": "={{`New order: ${$json.subject}`}}",
        "toEmail": "orders@company.com",
        "fromEmail": "noreply@company.com"
      },
      "name": "Notify Order Team",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 1,
      "position": [2200, 400]
    },
    {
      "parameters": {
        "message": "={{`New complaint: ${$json.subject}`}}",
        "toEmail": "support@company.com",
        "fromEmail": "noreply@company.com"
      },
      "name": "Notify Complaint Team",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 1,
      "position": [2200, 600]
    },
    {
      "parameters": {
        "labelNames": "={{$json.category}}",
        "markAsRead": True,
        "messageId": "={{$json.id}}"
      },
      "name": "Label and Archive",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 1,
      "position": [2400, 300]
    },
    {
      "parameters": {
        "database": "workflow",
        "table": "processed",
        "query": "INSERT INTO processed(id) VALUES({{$json.id}})"
      },
      "name": "Save Processed",
      "type": "n8n-nodes-base.database",
      "typeVersion": 1,
      "position": [2600, 300]
    },
    {
      "parameters": {"command": "echo failure >> /var/log/workflow_errors"},
      "name": "Log Error",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [2800, 300]
    }
  ],
  "connections": {
    "Gmail Trigger": {"main": [[{"node": "Split In Batches", "type": "main", "index": 0}]]},
    "Split In Batches": {"main": [[{"node": "Prepare Classification", "type": "main", "index": 0}], [{"node": "Split In Batches", "type": "main", "index": 0, "hook": "continue"}]]},
    "Prepare Classification": {"main": [[{"node": "ChatGPT Classify", "type": "main", "index": 0}]]},
    "ChatGPT Classify": {"main": [[{"node": "Parse Classification", "type": "main", "index": 0}]]},
    "Parse Classification": {"main": [[{"node": "Low Confidence?", "type": "main", "index": 0}]]},
    "Low Confidence?": {"main": [[{"node": "Mark Uncertain", "type": "main", "index": 0}], [{"node": "Check Duplicate", "type": "main", "index": 0}]]},
    "Mark Uncertain": {"main": [[{"node": "Check Duplicate", "type": "main", "index": 0}]]},
    "Check Duplicate": {"main": [[{"node": "New Email?", "type": "main", "index": 0}]]},
    "New Email?": {"main": [[{"node": "Airtable Quote", "type": "main", "index": 0}], [{"node": "Airtable Order", "type": "main", "index": 1}], [{"node": "Airtable Complaint", "type": "main", "index": 2}]]},
    "Airtable Quote": {"main": [[{"node": "Notify Quote Team", "type": "main", "index": 0}]]},
    "Airtable Order": {"main": [[{"node": "Notify Order Team", "type": "main", "index": 0}]]},
    "Airtable Complaint": {"main": [[{"node": "Notify Complaint Team", "type": "main", "index": 0}]]},
    "Notify Quote Team": {"main": [[{"node": "Label and Archive", "type": "main", "index": 0}]]},
    "Notify Order Team": {"main": [[{"node": "Label and Archive", "type": "main", "index": 0}]]},
    "Notify Complaint Team": {"main": [[{"node": "Label and Archive", "type": "main", "index": 0}]]},
    "Label and Archive": {"main": [[{"node": "Save Processed", "type": "main", "index": 0}]]},
    "Save Processed": {"main": [[{"node": "Split In Batches", "type": "main", "index": 1}]]},
    "Split In Batches": {"main": [None, [{"node": "Log Error", "type": "main", "index": 0}]]}
  }
}

with open('gmail_automation_workflow.json', 'w') as f:
    json.dump(workflow, f, indent=2)

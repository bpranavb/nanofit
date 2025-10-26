# Webhook URL Update - Complete ✅

## What Was Changed
Updated the n8n webhook URL for troubleshooting purposes.

### Old URL:
```
https://spantra.app.n8n.cloud/webhook/upload
```

### New URL:
```
https://spantra.app.n8n.cloud/webhook-test/upload
```

## Files Updated
1. **backend/server.py** (Line 61)
   - Changed `N8N_WEBHOOK_URL` constant
   
2. **N8N_WEBHOOK_INTEGRATION.md**
   - Updated documentation with new webhook URL
   
3. **test_result.md**
   - Updated problem statement and agent communication logs

## Backend Status
✅ Backend restarted successfully (PID: 1520)
✅ Application running without errors
✅ Webhook will now send data to the new URL

## Testing the New Webhook
When you click "Generate Try-On", the application will now send data to:
```
POST https://spantra.app.n8n.cloud/webhook-test/upload
```

With payload:
```json
{
  "tryon_id": "uuid",
  "timestamp": "ISO timestamp",
  "images": [
    {
      "type": "person",
      "data": "base64-string"
    },
    {
      "type": "clothing",
      "data": "base64-string"
    },
    {
      "type": "result",
      "data": "base64-string"
    }
  ]
}
```

## How to Monitor
Check backend logs for webhook activity:
```bash
tail -f /var/log/supervisor/backend.*.log | grep -i "webhook"
```

You should see:
- `INFO - Sending try-on data to n8n webhook for tryon_id: [uuid]`
- `INFO - Successfully sent data to n8n webhook. Status: [status_code]`

Or if there's an error:
- `ERROR - HTTP error sending to n8n webhook: [error message]`

## Next Steps
1. Configure your n8n workflow to accept requests at `/webhook-test/upload`
2. Test a try-on to verify the webhook receives data
3. Check the payload structure in n8n
4. Once confirmed working, you can switch back to the original URL if needed

## Need to Change URL Again?
Simply update line 61 in `backend/server.py`:
```python
N8N_WEBHOOK_URL = "https://your-new-url.com"
```

Then restart backend:
```bash
sudo supervisorctl restart backend
```

---
**Update completed at:** 2025-10-26 22:25 UTC

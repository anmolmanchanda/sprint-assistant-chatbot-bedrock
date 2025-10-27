# Deployment Guide - Sprint Report Assistant

## Deploying to Streamlit Cloud

### Step 1: Prepare Your Repository

1. Push all code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit: Sprint Report Assistant"
git remote add origin https://github.com/anmolmanchanda/sprint-report-assistant.git
git push -u origin main
```

### Step 2: Set Up Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `anmolmanchanda/sprint-report-assistant`
5. Set:
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: Choose a custom URL (e.g., `sprint-assistant`)

### Step 3: Configure AWS Secrets

Before deploying, you need to add AWS credentials as secrets:

1. In Streamlit Cloud, go to your app settings
2. Click on "Secrets" in the left sidebar
3. Add the following (replace with your actual credentials):

```toml
AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_KEY"
AWS_DEFAULT_REGION = "us-east-1"
```

### Step 4: Modify Code for Secrets

Update `src/embeddings.py`, `src/retrieval.py`, and `src/agent.py` to use Streamlit secrets:

```python
# At the top of each file, add:
import streamlit as st

# Replace AWS client initialization with:
if 'AWS_ACCESS_KEY_ID' in st.secrets:
    self.bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name=st.secrets.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
    )
else:
    # Fallback to default credentials
    self.bedrock = boto3.client(
        service_name="bedrock-runtime",
        region_name=aws_region
    )
```

### Step 5: Upload PDFs

Since Streamlit Cloud doesn't persist files, you have two options:

**Option A: Commit PDFs to repo** (if they're not sensitive)
```bash
git add data/*.pdf
git commit -m "Add sprint report PDFs"
git push
```

**Option B: Use S3** (recommended for sensitive data)
- Store PDFs in S3
- Modify `src/embeddings.py` to load from S3
- Add S3 bucket name to secrets

### Step 6: Pre-generate Vector Store

For faster deployment, commit the vector store:

1. Run locally first:
```bash
python src/embeddings.py
```

2. Commit the vector store:
```bash
git add chroma_db/
git commit -m "Add pre-generated vector store"
git push
```

**Note**: This increases repo size. For production, use persistent storage.

### Step 7: Deploy

1. Click "Deploy!" in Streamlit Cloud
2. Wait 2-3 minutes for deployment
3. Your app will be live at: `https://sprint-assistant.streamlit.app`

### Step 8: Test

1. Open your deployed URL
2. Test with example queries
3. Verify AWS credentials work
4. Check that PDFs are loaded correctly

## Custom Domain Setup (Optional)

To use your own domain (e.g., sprint-assistant.anmol.am):

1. In your domain DNS settings, add a CNAME record:
   - Name: `sprint-assistant`
   - Value: `sprint-assistant.streamlit.app`

2. In Streamlit Cloud app settings:
   - Go to "Settings" → "General"
   - Add your custom domain
   - Save changes

## Troubleshooting

### "Vector store not found"
- Make sure `chroma_db/` is committed to repo
- Or run the embeddings script in Streamlit Cloud console

### AWS Credentials Error
- Verify secrets are added correctly
- Check IAM permissions for Bedrock access
- Ensure region is correct

### App is slow
- Consider reducing number of PDFs
- Decrease chunk size in embeddings
- Use caching for frequent queries

## Monitoring

Streamlit Cloud provides:
- App analytics (viewers, interactions)
- Error logs
- Resource usage

Access these in your app dashboard.

## Updating the App

To update your deployed app:

```bash
git add .
git commit -m "Update: [describe changes]"
git push
```

Streamlit Cloud will automatically redeploy.

## Cost Considerations

- Streamlit Cloud: Free for public apps
- AWS Bedrock: Pay per use (~$0.01 per 1K requests)
- Total: <$5/month for demo usage

## Production Considerations

For production deployment:
- Use environment-specific configs
- Implement authentication
- Add CloudWatch logging
- Use Aurora/RDS for vector store
- Implement rate limiting
- Add error monitoring (Sentry)
- Use CI/CD pipeline

---

**Need help?** Check the [Streamlit Cloud docs](https://docs.streamlit.io/streamlit-community-cloud)

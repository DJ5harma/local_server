# AWS S3 Setup Guide for SV30 System

## 📋 Overview

This guide will help you configure AWS S3 for uploading SV30 test data (videos, images, results).

---

## 🔧 Step 1: Create AWS Account

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow registration process (requires credit card)
4. Free tier includes:
   - 5 GB S3 storage
   - 20,000 GET requests
   - 2,000 PUT requests per month

---

## 📦 Step 2: Create S3 Bucket

### Via AWS Console (Web Interface):

1. **Log in to AWS Console**
   - Go to https://console.aws.amazon.com
   - Sign in with your credentials

2. **Navigate to S3**
   - Search for "S3" in services
   - Click "S3"

3. **Create Bucket**
   - Click "Create bucket"
   - **Bucket name**: `sv30-test-data` (must be globally unique)
     - If taken, try: `sv30-test-data-yourcompany`
   - **Region**: Choose closest region
     - Mumbai: `ap-south-1`
     - Singapore: `ap-southeast-1`
   - **Block Public Access**: Keep all boxes CHECKED (security)
   - Click "Create bucket"

### Via AWS CLI (Optional):

```bash
aws s3 mb s3://sv30-test-data --region ap-south-1
```

---

## 🔐 Step 3: Create IAM User with S3 Access

### Why IAM User?
Never use root account credentials in scripts. Create a dedicated user with limited permissions.

### Steps:

1. **Go to IAM Service**
   - In AWS Console, search for "IAM"
   - Click "Identity and Access Management (IAM)"

2. **Create User**
   - Click "Users" in left menu
   - Click "Create user"
   - **User name**: `sv30-uploader`
   - **Access type**: Check "Access key - Programmatic access"
   - Click "Next"

3. **Set Permissions**
   - Click "Attach policies directly"
   - Search for: `AmazonS3FullAccess`
   - Check the box
   - Click "Next"

4. **Review and Create**
   - Review settings
   - Click "Create user"

5. **Save Credentials**
   - **IMPORTANT**: Download or copy these immediately
   - **Access Key ID**: (e.g., `AKIAIOSFODNN7EXAMPLE`)
   - **Secret Access Key**: (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
   - **You cannot retrieve the secret key again!**

---

## 🖥️ Step 4: Install AWS CLI (Optional but Recommended)

### On Raspberry Pi:

```bash
# Install AWS CLI
sudo apt update
sudo apt install awscli -y

# Verify installation
aws --version
```

### Configure AWS CLI:

```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID: <your_access_key_id>
AWS Secret Access Key: <your_secret_access_key>
Default region name: ap-south-1
Default output format: json
```

---

## 🔑 Step 5: Configure SV30 System

### Option A: Using Environment Variables (Recommended)

Add to your `.bashrc` or `.profile`:

```bash
nano ~/.bashrc
```

Add these lines:
```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCY"
```

Save and reload:
```bash
source ~/.bashrc
```

### Option B: Direct Configuration in sv30config.py

Edit `sv30config.py`:

```python
# AWS Credentials (NOT RECOMMENDED - use environment variables instead)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCY"
AWS_REGION = "ap-south-1"

# S3 Bucket Configuration
AWS_S3_BUCKET = "sv30-test-data"
```

**⚠️ WARNING: Never commit credentials to Git!**

---

## ⚙️ Step 6: Enable AWS in SV30 Config

Edit `sv30config.py`:

```python
# Enable AWS
AWS_ENABLED = True

# S3 Bucket Configuration
AWS_S3_BUCKET = "sv30-test-data"  # Your bucket name
AWS_S3_PREFIX = "sv30_tests"      # Folder in bucket

# Upload settings
AWS_UPLOAD_VIDEO = True           # Upload raw video
AWS_UPLOAD_IMAGES = True          # Upload Camera 2 snapshots
AWS_UPLOAD_RESULTS = True         # Upload JSON and graphs
AWS_DELETE_AFTER_UPLOAD = True    # Delete local files after upload (production)
```

---

## 🧪 Step 7: Test Configuration

### Test 1: Verify Credentials

```bash
# List S3 buckets
aws s3 ls

# Should show your bucket
# 2024-12-19 14:30:45 sv30-test-data
```

### Test 2: Manual Upload Test

```bash
# Create test file
echo "Test upload" > test.txt

# Upload to S3
aws s3 cp test.txt s3://sv30-test-data/test/test.txt

# Verify upload
aws s3 ls s3://sv30-test-data/test/

# Delete test file
aws s3 rm s3://sv30-test-data/test/test.txt
```

### Test 3: Python boto3 Test

```bash
python3 << EOF
import boto3
s3 = boto3.client('s3')
buckets = s3.list_buckets()
print("Buckets:", [b['Name'] for b in buckets['Buckets']])
EOF
```

---

## 📁 S3 Folder Structure

Your test data will be organized as:

```
sv30-test-data/
└── sv30_tests/
    └── 191224/                    # Date folder (DDMMYY)
        └── 191224_143045test1/    # Test ID folder
            ├── 191224_143045test1.mp4   # Video
            ├── cam2_t0.jpg               # RGB snapshot t=0
            ├── cam2_t30.jpg              # RGB snapshot t=30
            ├── sv30_metrics.json         # Metrics
            ├── rgb_values.json           # RGB analysis
            ├── sludge_height_vs_time.png # Graph 1
            ├── sv30_vs_time.png          # Graph 2
            ├── inst_velocity_vs_time.png # Graph 3
            ├── avg_velocity_vs_time.png  # Graph 4
            └── dashboard_combined.png    # Graph 5
```

---

## 🔍 Step 8: Monitor Uploads

### Via AWS Console:

1. Go to S3 service
2. Click your bucket name
3. Navigate folders to see uploaded files

### Via AWS CLI:

```bash
# List all test dates
aws s3 ls s3://sv30-test-data/sv30_tests/

# List specific date
aws s3 ls s3://sv30-test-data/sv30_tests/191224/

# List specific test
aws s3 ls s3://sv30-test-data/sv30_tests/191224/191224_143045test1/
```

---

## 💰 Cost Estimation

### Storage Costs (Mumbai region):
- First 50 TB: $0.023 per GB per month
- **Example**: 30 min video (~2 GB) + images/results = ~2.1 GB
- **3 tests/day × 30 days** = 189 GB
- **Monthly cost**: 189 GB × $0.023 = ~$4.35

### Data Transfer:
- Upload (PUT): **FREE** (ingress)
- Download (GET): First 10 TB $0.09/GB

### Total Estimated Monthly Cost:
- **Light use** (1 test/day): ~$1.50/month
- **Moderate use** (3 tests/day): ~$4.50/month
- **Heavy use** (10 tests/day): ~$15/month

**Tip**: Set up billing alerts in AWS!

---

## 🛡️ Security Best Practices

### 1. Use IAM User (Not Root Account)
✅ **DO**: Create dedicated IAM user
❌ **DON'T**: Use root account credentials

### 2. Limit Permissions
Only grant S3 access, not full AWS access:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::sv30-test-data",
        "arn:aws:s3:::sv30-test-data/*"
      ]
    }
  ]
}
```

### 3. Rotate Access Keys
Change access keys every 90 days

### 4. Enable MFA
Enable Multi-Factor Authentication on AWS account

### 5. Enable S3 Versioning (Optional)
Protects against accidental deletion:
```bash
aws s3api put-bucket-versioning \
  --bucket sv30-test-data \
  --versioning-configuration Status=Enabled
```

---

## 🔧 Troubleshooting

### Error: "NoCredentialsError"
**Problem**: AWS credentials not found

**Solution**:
```bash
# Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# If empty, export them
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
```

### Error: "AccessDenied"
**Problem**: IAM user lacks permissions

**Solution**:
- Go to IAM → Users → sv30-uploader
- Attach `AmazonS3FullAccess` policy

### Error: "BucketAlreadyExists"
**Problem**: Bucket name taken

**Solution**: Choose unique bucket name
```python
AWS_S3_BUCKET = "sv30-test-data-yourcompany123"
```

### Error: "RequestTimeTooSkewed"
**Problem**: System clock is wrong

**Solution**:
```bash
sudo apt install ntpdate
sudo ntpdate -s time.nist.gov
```

### Slow Uploads
**Problem**: Large video files taking too long

**Solution 1**: Use multipart upload (automatic in boto3 for files >5MB)

**Solution 2**: Compress video before upload:
```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -preset fast output.mp4
```

---

## 🧹 Data Lifecycle Management

### Automatic Deletion After X Days

To save costs, auto-delete old data:

1. Go to S3 → Your bucket
2. Click "Management" tab
3. Click "Create lifecycle rule"
4. Name: "Delete old tests"
5. Prefix: `sv30_tests/`
6. Check "Expire current versions"
7. Days: `90` (delete after 90 days)
8. Save

### Manual Cleanup

```bash
# Delete tests older than 30 days
aws s3 rm s3://sv30-test-data/sv30_tests/ \
  --recursive \
  --exclude "*" \
  --include "$(date -d '30 days ago' +%d%m%y)*"
```

---

## 📊 Download Data from S3

### Single File:
```bash
aws s3 cp s3://sv30-test-data/sv30_tests/191224/191224_143045test1/191224_143045test1.mp4 .
```

### Entire Test:
```bash
aws s3 cp s3://sv30-test-data/sv30_tests/191224/191224_143045test1/ . --recursive
```

### All Tests from Date:
```bash
aws s3 cp s3://sv30-test-data/sv30_tests/191224/ . --recursive
```

---

## ✅ Final Checklist

Before running full pipeline:

- [ ] AWS account created
- [ ] S3 bucket created
- [ ] IAM user created with S3 access
- [ ] Access keys saved securely
- [ ] boto3 installed (`pip install boto3`)
- [ ] Credentials configured (env vars or config file)
- [ ] `AWS_ENABLED = True` in sv30config.py
- [ ] Bucket name updated in sv30config.py
- [ ] Test upload successful
- [ ] Billing alerts set up

---

## 🚀 Ready to Use!

Your SV30 system is now configured for AWS S3 uploads!

Run full pipeline:
```bash
python3 main.py full
```

After 30 minutes, check S3 bucket for uploaded data.

---

## 📞 Support

If you encounter issues:
1. Check AWS CloudWatch logs
2. Review error messages in terminal
3. Verify IAM permissions
4. Check network connectivity
5. Ensure system time is correct

For AWS-specific issues, check: https://docs.aws.amazon.com/s3/

# 🚀 Streamlit Cloud Deployment Guide

This guide will help you deploy your **LabOps Metrics Starter Kit** (including the integrated Micro-PoCs) to Streamlit Cloud.

## 📋 Prerequisites

- A GitHub account
- A Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- Your code pushed to a GitHub repository

## 🔧 Repository Setup

### 1. Ensure Your Repository Structure

Your repository should have this structure for Streamlit Cloud deployment:

```
labops-metrics-starter-kit/
├── streamlit_app.py          # Main Streamlit application (root level)
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── sample_dq_rules.yaml     # Sample DQ rules
├── app/                     # Core application code
├── scripts/                 # Micro-PoC scripts
└── README.md               # Documentation
```

### 2. Verify Key Files

- ✅ **`streamlit_app.py`** - Main app with 3 tabs (Metrics, Data Quality, Teams Bot)
- ✅ **`requirements.txt`** - All dependencies including `pyyaml`, `seaborn`, `plotly`
- ✅ **`.streamlit/config.toml`** - Production-optimized configuration
- ✅ **`sample_dq_rules.yaml`** - Sample data quality rules

## 🌐 Deploy to Streamlit Cloud

### Step 1: Push to GitHub

```bash
# Ensure all changes are committed and pushed
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 2: Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Configure your app:

   **Repository:** `yourusername/labops-metrics-starter-kit`
   
   **Branch:** `main`
   
   **Main file path:** `streamlit_app.py`
   
   **App URL:** `labops-metrics-starter-kit` (or your preferred name)

### Step 3: Deploy

Click **"Deploy!"** and wait for the build to complete.

## 🔍 What Gets Deployed

Your deployed app will include:

### 📊 **Metrics Dashboard Tab**
- Real-time laboratory metrics
- TAT, throughput, and error rate monitoring
- Interactive charts and data tables
- Sample data generation for demonstration

### 🔍 **Data Quality Tab**
- CSV file upload and validation
- Built-in sample rules
- Custom YAML rules support
- Violation reporting and visualization

### 🤖 **Teams Bot Tab**
- Stand-up update creation
- Multiple input methods (manual, JSON, templates)
- Teams webhook configuration
- Dry-run mode for testing

## ⚙️ Configuration Options

### Environment Variables (Optional)

You can set these in Streamlit Cloud for enhanced functionality:

- `TEAMS_WEBHOOK_URL` - Your Microsoft Teams webhook URL
- `DATABASE_URL` - Database connection string (if using external DB)

### Customization

- **Theme colors** - Edit `.streamlit/config.toml`
- **Sample data** - Modify `create_sample_data()` function
- **DQ rules** - Update `sample_dq_rules.yaml`

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check that file paths are correct

2. **File Not Found Errors**
   - Verify `sample_dq_rules.yaml` exists in root directory
   - Check file permissions

3. **Memory Issues**
   - Reduce sample data size in `create_sample_data()`
   - Optimize chart rendering

### Build Logs

Check Streamlit Cloud build logs for specific error messages:
1. Go to your app in Streamlit Cloud
2. Click **"Manage app"**
3. View **"Build logs"** for detailed error information

## 🔄 Updates and Maintenance

### Updating Your App

1. Make changes locally
2. Test with `streamlit run streamlit_app.py`
3. Commit and push to GitHub
4. Streamlit Cloud automatically redeploys

### Monitoring

- Check app performance in Streamlit Cloud dashboard
- Monitor resource usage
- Review user feedback and analytics

## 🌟 Features in Production

### ✅ **Working Features**
- Complete metrics dashboard with sample data
- Data quality validation engine
- Teams stand-up bot interface
- Responsive design and modern UI
- File upload and processing
- Interactive charts and visualizations

### 🔧 **Simulated Features** (for demo purposes)
- Data quality validation (simulated API calls)
- Teams posting (dry-run mode)
- Database operations (sample data generation)

## 📱 Access Your Deployed App

Once deployed, your app will be available at:
```
https://labops-metrics-starter-kit.streamlit.app/
```

## 🎯 Next Steps

After successful deployment:

1. **Test all functionality** - Verify each tab works correctly
2. **Configure Teams webhook** - Set up real Teams integration
3. **Customize rules** - Modify DQ rules for your use case
4. **Share with team** - Invite colleagues to use the dashboard
5. **Monitor usage** - Track app performance and user engagement

## 🆘 Support

If you encounter issues:

1. Check the build logs in Streamlit Cloud
2. Verify your local setup works
3. Review the error messages for specific issues
4. Check that all dependencies are compatible

---

**🎉 Congratulations!** Your LabOps Metrics Starter Kit is now deployed and accessible to users worldwide through Streamlit Cloud.

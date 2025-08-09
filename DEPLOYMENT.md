# 🚀 GitHub Pages Deployment Guide

This guide will walk you through setting up GitHub Pages for your LabOps Metrics Starter Kit repository.

## 📋 Prerequisites

- A GitHub account
- Your repository pushed to GitHub
- GitHub Pages enabled on your repository

## 🔧 Step-by-Step Setup

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Scroll down to **Pages** section (or click **Pages** in the left sidebar)
4. Under **Source**, select **Deploy from a branch**
5. Choose **main** branch and **/docs** folder
6. Click **Save**

### 2. Configure Repository Settings

1. In **Settings** → **Actions** → **General**
2. Ensure **Actions permissions** is set to **Allow all actions and reusable workflows**
3. Scroll down to **Workflow permissions**
4. Check **Read and write permissions**
5. Check **Allow GitHub Actions to create and approve pull requests**
6. Click **Save**

### 3. Update Configuration Files

**Important**: Update these files with your actual GitHub username:

#### Update `docs/_config.yml`:
```yaml
url: "https://yourusername.github.io"
baseurl: "/labops-metrics-starter-kit"
```

#### Update `docs/index.html`:
Replace all instances of `yourusername` with your actual GitHub username in the GitHub links.

### 4. Push Changes

```bash
git add .
git commit -m "Add GitHub Pages configuration"
git push origin main
```

### 5. Monitor Deployment

1. Go to **Actions** tab in your repository
2. You should see the **Deploy to GitHub Pages** workflow running
3. Wait for it to complete (usually 2-3 minutes)
4. Check the deployment status

## 🌐 Access Your Site

Once deployed, your site will be available at:
```
https://yourusername.github.io/labops-metrics-starter-kit
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Pages Not Showing
- Check if GitHub Pages is enabled in Settings
- Verify the source branch and folder are correct
- Wait a few minutes for initial deployment

#### 2. Workflow Fails
- Check the Actions tab for error details
- Verify workflow permissions are set correctly
- Ensure the `docs/` folder exists and contains files

#### 3. Site Not Updating
- Check if the workflow completed successfully
- Verify changes were pushed to the main branch
- Wait 5-10 minutes for changes to propagate

### Debugging Steps

1. **Check Actions Logs**:
   - Go to Actions tab
   - Click on the failed workflow
   - Review the error messages

2. **Verify File Structure**:
   ```
   docs/
   ├── index.html
   ├── _config.yml
   ├── README.md
   ├── ARCHITECTURE.md
   ├── ROADMAP.md
   └── DEMO_SCRIPT.md
   ```

3. **Check Permissions**:
   - Repository settings → Actions → General
   - Ensure proper permissions are set

## 🎨 Customization

### Modify the Landing Page

Edit `docs/index.html` to:
- Change colors and styling
- Add your logo
- Modify content and features
- Update links and references

### Add More Pages

1. Create new HTML files in the `docs/` folder
2. Add navigation links in `index.html`
3. Update `_config.yml` if needed
4. Push changes to trigger deployment

### Custom Domain (Optional)

1. In Pages settings, add your custom domain
2. Update DNS records as instructed
3. Update `_config.yml` with the new URL

## 📱 Testing Locally

Before pushing to GitHub, test your changes locally:

```bash
# Install Jekyll (requires Ruby)
gem install jekyll bundler

# Navigate to docs directory
cd docs

# Start local server
jekyll serve

# Open http://localhost:4000 in your browser
```

## 🔄 Continuous Deployment

The setup includes automatic deployment:
- Every push to `main` branch triggers deployment
- Manual deployment available via Actions tab
- Deployment status visible in repository Actions

## 📊 Monitoring

Monitor your deployment:
- **Actions tab**: View workflow runs and status
- **Pages settings**: Check deployment status
- **Site URL**: Verify site is accessible and updated

## 🆘 Getting Help

If you encounter issues:

1. Check the [GitHub Pages documentation](https://docs.github.com/en/pages)
2. Review the workflow logs in Actions tab
3. Verify all configuration files are correct
4. Create an issue in your repository

## 🎯 Next Steps

After successful deployment:

1. **Share your site**: Send the URL to stakeholders
2. **Customize content**: Update with your specific information
3. **Add analytics**: Consider adding Google Analytics or similar
4. **Monitor performance**: Use GitHub's built-in analytics

---

**Note**: The first deployment may take 5-10 minutes. Subsequent updates are usually faster (2-3 minutes).

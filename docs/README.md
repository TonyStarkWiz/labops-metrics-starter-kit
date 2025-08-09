# LabOps Metrics Starter Kit - Documentation

This directory contains the documentation and web assets for the LabOps Metrics Starter Kit project.

## 📚 Documentation Structure

- **[`index.html`](index.html)** - Main project showcase page (GitHub Pages homepage)
- **[`ARCHITECTURE.md`](ARCHITECTURE.md)** - System architecture documentation
- **[`ROADMAP.md`](ROADMAP.md)** - Development roadmap and future plans
- **[`DEMO_SCRIPT.md`](DEMO_SCRIPT.md)** - 5-minute demo script for presentations

## 🌐 GitHub Pages Setup

This project is configured to automatically deploy to GitHub Pages using GitHub Actions.

### Automatic Deployment

1. **Push to main branch** - The `deploy.yml` workflow automatically builds and deploys
2. **Manual deployment** - Use the "workflow_dispatch" trigger in GitHub Actions
3. **Deployment URL** - Available at `https://yourusername.github.io/labops-metrics-starter-kit`

### Configuration Files

- **`.github/workflows/deploy.yml`** - GitHub Actions deployment workflow
- **`docs/_config.yml`** - Jekyll configuration for GitHub Pages
- **`docs/index.html`** - Main HTML page with modern styling

## 🚀 Local Development

To test the documentation locally:

```bash
# Install Jekyll (if you have Ruby)
gem install jekyll bundler

# Navigate to docs directory
cd docs

# Start local server
jekyll serve

# Open http://localhost:4000 in your browser
```

## 📱 Features

The main documentation page includes:

- **Responsive Design** - Works on desktop, tablet, and mobile
- **Modern UI** - Clean, professional appearance with animations
- **Quick Start Guide** - Copy-paste commands to get started
- **Feature Showcase** - Interactive cards highlighting key capabilities
- **Technology Stack** - Visual representation of used technologies
- **Navigation** - Easy access to all documentation

## 🔧 Customization

To customize the GitHub Pages site:

1. **Update URLs** - Modify `_config.yml` with your actual GitHub username
2. **Modify Styling** - Edit CSS in `index.html` to match your brand
3. **Add Content** - Extend the HTML with additional sections or features
4. **Update Links** - Ensure all GitHub links point to your repository

## 📊 Performance

- **Fast Loading** - Optimized CSS and minimal JavaScript
- **SEO Friendly** - Proper meta tags and semantic HTML
- **Accessible** - Follows web accessibility guidelines
- **Mobile First** - Responsive design for all devices

## 🆘 Troubleshooting

If GitHub Pages deployment fails:

1. Check the GitHub Actions workflow for errors
2. Verify the `docs/` directory contains valid files
3. Ensure the repository has Pages enabled in Settings
4. Check that the workflow has proper permissions

## 📞 Support

For issues with the documentation or deployment:

- Create an issue in the main repository
- Check the GitHub Actions logs
- Review the Jekyll configuration
- Verify file paths and permissions


### GitHubActionsGitPages

**Reference**
- Documentation: https://github.com/actions/starter-workflows/blob/main/pages/static.yml

**Implementation Guide**

Create `.github/workflows/deploy.yml` in the project root:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "pnpm"

      - name: Setup pnpm
        uses: pnpm/action-setup@v3
        with:
          version: 8

      - name: Install Dependencies
        run: pnpm install

      - name: Build
        run: pnpm build

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload Artifact
        uses: actions/upload-pages-artifact@v3
        with:
          # Adjust path to your build output directory (e.g., apps/web/dist)
          path: './dist' 

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

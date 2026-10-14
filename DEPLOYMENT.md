# Put Pastpaper AI online with Render

The updated app is on the `pastpaper-web` branch of `its4jeremy/my-python`. A hosted service runs independently of your Windows computer. No AI API key is needed to serve this bank.

## Test before paying

Download the branch through GitHub, extract it, and double-click `START_WEBSITE.bat`. Browse the topics, open original diagrams and answers, try the glossary controls, and search. The full collection has also passed automated data/web tests and desktop/mobile Chromium checks in the cloud workspace.

Hosting has not been created or purchased. The included `render.yaml` selects a free service for optional online validation. Free services can sleep after inactivity; review Render’s current plan terms. A continuously running service uses a paid instance. The earlier choice of paid hosting with a persistent disk remains a separate deployment step after you are happy with the site.

## Deploy through the browser

1. Sign in at https://dashboard.render.com and connect the GitHub account that owns the repository.
2. Choose **New → Web Service**, select `its4jeremy/my-python`, and choose the **pastpaper-web** branch. Keep the whole repository: database, processed JSON, glossary, source catalogue, source PDFs, reference PDFs and shared images are used by the app.
3. Choose Python. Build command: `pip install -r requirements.txt`. Start command: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --access-logfile - --error-logfile - app:app`. Health check path: `/topics`.
4. Review the selected instance type and price before creating the service. Render assigns the public HTTPS URL when deployed. Validate topics, search, the glossary and original PDFs using that actual URL.

Alternatively, a Blueprint can use `render.yaml`; ensure it selects the `pastpaper-web` branch rather than the unmodified application files on `main`.

The present website is read-only and restores its committed SQLite bank on each deployment. It can operate without a persistent disk. If you want the hosted database to receive updates independently of GitHub, the persistent-disk deployment needs a configurable database path and one-time initialization that preserves existing data; those settings have not been enabled in this blueprint. The site currently has no browser-based paper uploader or import console.

New updates to the connected GitHub branch can trigger redeployment. Your local terminal and computer do not need to remain running. Local validation does not establish a successful deployment to your Render account.

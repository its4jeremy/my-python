# Put Pastpaper AI online with Render

This configuration runs the website on Render, independent of your Windows computer. You manage the service through Render's website. No AI API key is needed to serve the existing question bank.

## Deploy through the browser

1. Upload `app.py`, `requirements.txt`, `render.yaml`, the `templates` folder, and the `static` folder to the root of your GitHub repository. Keep the existing `pastpapers.db` there. GitHub's **Add file → Upload files** page can accept files and folders dragged from Explorer. Do not upload `venv` or `.env`.
2. Sign in at https://dashboard.render.com and connect the GitHub account that owns the repository.
3. Choose **New → Blueprint**, select `its4jeremy/my-python`, and use the `main` branch. Review the free service declared in `render.yaml` and deploy it. If Blueprint is unavailable, choose **New → Web Service**, select the same repository, set the build command to `pip install -r requirements.txt`, and set the start command to `gunicorn --bind 0.0.0.0:$PORT --workers 2 --access-logfile - --error-logfile - app:app`. Choose Python and the Free instance type.
4. When deployment finishes, open the HTTPS URL shown by Render. Check the home page, topics, a question's mark scheme, and search for `recursion`.

The exact public URL is assigned by Render; the project name may already be taken. This project has been validated locally with Gunicorn; that does not establish a successful deployment to your account.

## Free versus continuously running hosting

The included blueprint selects the free plan and does not purchase a service. Free services can sleep after inactivity and take time to wake up. Check Render's current plan terms before deployment. For a site that stays running, select a paid instance in the dashboard after reviewing its price.

The current site only reads the database shipped in GitHub. It therefore does not need a persistent disk: every deployment restores the committed question bank. To add new questions, update `pastpapers.db` in the repository and redeploy. This app does not include a browser-based uploader or AI processing page.

If you later add online imports or database writes, arrange persistent storage before enabling them; runtime changes on a free service's filesystem are not durable. A paid persistent disk needs a configurable database path and initialization procedure; the current blueprint does not configure that feature.

GitHub updates to the connected branch can trigger redeployment. Your local terminal and computer do not have to stay running.

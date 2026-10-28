# News assistant front-end

React/Vite interface for the Assignment 3 local LLM safety prototype.
Use Node.js 24 and the exact dependencies from package-lock.json.

```bash
npm ci
npm run lint
npm run build
```

From the repository root, start the server with `python site/server.py`.
It serves `site/web/dist/` at http://127.0.0.1:8765/ and forwards chat requests to
local Ollama. For development, keep that server running and use `npm run dev`
in this directory; Vite proxies /api to the Python server.

Both chat views include a model/defence selector. The full-page chat stores each
conversation and its mode in browser localStorage. The floating chat starts a
fresh conversation when its mode changes.

See the [project README](../../README.md) for model installation, results and
limitations. Dependencies and generated builds are excluded from Git.

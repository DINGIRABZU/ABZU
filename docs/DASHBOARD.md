# Metrics Dashboard

This dashboard visualises recent model performance and the predicted best LLM.

## Setup

Install dependencies and run the dashboard:

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

The application reads from `INANNA_AI/db_storage.py` and updates automatically
when new benchmarks are logged.

## Web Console Stream

Launch `start_spiral_os.py` and open `web_console/index.html` in your browser.
The page connects to the `/offer` endpoint using WebRTC and plays the live
avatar feed provided by `video_stream.py`.

## Dashboard and Operator Console

Both interfaces use the `WEB_CONSOLE_API_URL` environment variable. Set it to
the FastAPI base endpoint such as `http://localhost:8000/glm-command`. The
operator console automatically removes the trailing path when connecting.

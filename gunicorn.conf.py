# Gunicorn reads this file automatically when it is started from the project
# root (e.g. `gunicorn smart_test_platform.wsgi`). Options passed on the
# command line still win.

# Teacher-side AI requests (test from a lecture or topic, AI-assisted upload,
# SCAFFOLD lesson design) make several OpenRouter calls in one request. The
# default 30 s timeout would kill the worker mid-generation and the teacher
# would get a 502.
timeout = 300
graceful_timeout = 30

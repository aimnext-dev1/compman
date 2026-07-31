#!/bin/sh
PORT=${PORT:-18080}
echo "Starting compman seed daemon server on port $PORT..."
mkdir -p /www
cat <<EOF > /www/index.html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>compman seed daemon</title>
    <style>
        body { font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #0f172a; color: #f8fafc; }
        .card { background: #1e293b; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; border: 1px solid #334155; }
        h1 { color: #38bdf8; margin-bottom: 0.5rem; }
        p { color: #94a3b8; font-size: 1.1rem; }
        .tag { display: inline-block; background: #0284c7; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 compman Seed Daemon</h1>
        <p>Status: <span class="tag">RUNNING</span></p>
        <p>Message: <strong>${MESSAGE:-hello}</strong></p>
    </div>
</body>
</html>
EOF

exec httpd -f -p $PORT -h /www

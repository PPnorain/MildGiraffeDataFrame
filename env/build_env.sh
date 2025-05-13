export UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install uv
uv -v pip install -r ../requirements.txt  --system
uv -v pip install -r ../requirements_server.txt  --system
cd dependence_env
bash ttf.sh

name: 自动更新 V2Ray 节点

on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-and-run:
    runs-on: ubuntu-latest

    steps:
      - name: 检出仓库代码
        uses: actions/checkout@v4

      - name: 配置 Python 环境
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 安装依赖库
        run: |
          python -m pip install --upgrade pip
          pip install requests

      - name: 执行节点抓取脚本
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python fetch_nodes.py

      - name: 提交并推送到仓库
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "41898282+github-actions[bot]@://github.com"
          
          git add .
          
          git diff --cached --quiet && exit 0
          
          git commit -m "自动更新节点列表: $(date +'%Y-%m-%d %H:%M:%S')"
          git push

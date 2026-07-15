import os

def fetch():
    # 模拟的节点数据，后续可以改为真实的爬虫
    mock_nodes = [
        "vmess://ewogICJ2IjogIjIiLAogICJwcyI6ICLO9mS91yIsCiAgImFkZCI6ICIxMjcuMC4wLjEiLAogICJwb3J0IjogNDQzLAogICJpZCI6ICJ1dWlkIiwKICAiYWlkIjogMCwKICAibmV0IjogIndzIiwKICAidHlwZSI6ICJub25lIiwKICAiaG9zdCI6ICIiLAogICJwYXRoIjogIiIsCiAgInRscyI6ICJ0bHMiCn0=",
        "ss://YWVzLTI1Ni1nY206cGFzc3dvcmRAMTI3LjAuMC4xOjgzODg=#测试节点"
    ]
    with open("nodes.txt", "w", encoding="utf-8") as f:
        for node in mock_nodes:
            f.write(node + "\n")
    print("节点同步成功，已写入 nodes.txt")

if __name__ == "__main__":
    fetch()

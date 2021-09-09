1. 下载并安装 miniconda  https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-x86_64.sh
2. 安装依赖包  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
3. 服务注册 [简洁的 systemd 操作指南Linux下Service文件服务说明](https://www.huaweicloud.com/articles/97b99a007be6cb5063f3de2eaa6b752e.html)
```angular2
1. 将EtcPay.service复制到 /etc/systemd/system/目录下
2. 执行： sudo systemctl daemon-reload
3. 执行： sudo systemctl enable EtcPay.service
4. 启动： sudo systemctl start EtcPay
5. 终止： sudo systemctl stop EtcPay
```
 
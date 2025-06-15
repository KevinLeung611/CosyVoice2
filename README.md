# CosyVoice2
**原仓库地址：** [CosyVoice](https://github.com/FunAudioLLM/CosyVoice?tab=readme-ov-file)

据 CosyVoice 官方的描述，CosyVoice 二代模型比一代模型提供更快，更准，更稳定的语音生成能力。

但是使用起来发现交互方式并没有完全适配 CosyVoice的二代模型，特别不方便，特此我 clone 了官方的源码，做了一些改造。

**改造点主要有:**

1. 交互方式全部改成只适配 CosyVoice2 模型
2. 优化 UI 交互，提供更清晰的操作 UI
3. 取消生成语音时的流式返回，因为调用api时会有问题

## Demo

![Demo](asset/demo.png)

## 使用方法
开箱即用，可以参考 CosyVoice 的[官方文档](https://github.com/FunAudioLLM/CosyVoice)，
本仓库提供了下载模型的脚本(init.py)，不用自己创建了，因为只支持 CosyVoice2，因此只需要下载这个模型就可以了(可以节省很多磁盘空间)。

下面是官方提供的初始化流程: 

### Clone and install

- Clone the repo
    ``` sh
    git clone --recursive https://github.com/KevinLeung611/CosyVoice2.git
    # If you failed to clone the submodule due to network failures, please run the following command until success
    cd CosyVoice2
    git submodule update --init --recursive
    ```

- Install Conda: please see https://docs.conda.io/en/latest/miniconda.html
- Create Conda env:

    ``` sh
    conda create -n cosyvoice -y python=3.10
    conda activate cosyvoice
    # pynini is required by WeTextProcessing, use conda to install it as it can be executed on all platforms.
    conda install -y -c conda-forge pynini==2.1.5
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
    
    # If you encounter sox compatibility issues
    # ubuntu
    sudo apt-get install sox libsox-dev
    # centos
    sudo yum install sox sox-devel
    ```

Optionally, you can unzip `ttsfrd` resouce and install `ttsfrd` package for better text normalization performance.

Notice that this step is not necessary. If you do not install `ttsfrd` package, we will use WeTextProcessing by default.

``` sh
cd pretrained_models/CosyVoice-ttsfrd/
unzip resource.zip -d .
pip install ttsfrd_dependency-0.1-py3-none-any.whl
pip install ttsfrd-0.4.2-cp310-cp310-linux_x86_64.whl
```

项目环境初始化完成后，执行模型下载的脚本

```shell
# Download the CosyVoice2 model
python init.py
```

下载好模型之后，使用官方提供的 webui.py 脚本启动，这里不需要指定端口和模型，端口默认使用Gradio设置的7860。

```shell
# Launch the server
python webui.py
```


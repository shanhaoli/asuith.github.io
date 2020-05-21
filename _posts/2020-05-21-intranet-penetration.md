---
layout: article
keywords: NPS, SSH, Jupyter, TensorBoard
title: "使用NPS内网穿透，方便炼丹"
description: "你实验室的服务器也没有公网IP吗？"
date: "2020-05-21 15:15:53 +0800"
categories: cs
---

> {{ page.description }}

<!--more-->

照例先骂一波深圳大学城：VPN难用的要死，服务器也不给分公网IP。有道是，能力越大，责任越大；权利越多，责任越少。

不过有山就有路，我们可以使用内网穿透这种工具来进行，唔，内网穿透。常用的内网穿透工具有[frp](https://github.com/fatedier/frp)以及[NPS](https://github.com/ehang-io/nps)。frp配置复杂，很容易就不知道自己哪里出错了，不过网上已有较多参考资源。NPS配置更为方便，所以本文使用NPS来进行内网穿透，方便~~炼丹~~科研工作，并且将深度学习中常用的SSH、Jupyter以及TensorBoard做为使用例子。

## 原理、术语及要求

内网穿透的原理就是找一个有公网的服务器，作为中间的传话筒。虽然我们无法和内网的服务器直接沟通，但是我们和内网服务器的消息可以传到公网服务器，通过后者进行转发。

为了方便理解和操作，提前说明一下定义：

本地指的是使用者所处的环境（比如你在用的电脑），公网服务器是指有公网IP的服务器（比如阿里云、腾讯云、AWS、Google Cloud的云服务器），内网服务器是指有位于内网、且能够上网的服务器（比如实验室的电脑、服务器）。

不难推断出为，我们需要一个公网服务器，而且推荐国内的服务器，这样延迟会低很多。还有你应当懂得如何使用SSH，至少能看懂下面脚本在做什么以及键盘上`ctr` `C` `V`等按键完好。

登陆服务器可以使用`ssh`(\*Unix系统的命令行工具)，以及Putty软件（Windows系统下工具）。

上传的软件可以使用ftp软件、`scp`等工具。

## 配置NPS

### 服务端和客户端的选择

NPS在[GitHub](https://github.com/ehang-io/nps)的[Releases](https://github.com/ehang-io/nps/releases)上有很多版本，但是需要根据运行环境来进行下载两个包。

其中后缀为`\_server`的服务端应当在公网服务器运行，后缀为`\_client`的客户端应当在内网服务器运行。

至于前缀的选择，一般服务器应该是`amd64`架构，如果不确定可以算一卦。

这里我们假设为公网服务器选择了*linux_amd64_server.tar.gz*，为内网服务器选择了*linux_arm64_client.tar.gz*（皆为*v0.26.7*版本）。

### 服务端的安装及配置

接下来我们登陆服务器端，下载安装包。

当然，由于网络原因，你也可以选择下载到本地，然后上传至服务器。如果是自行上传，那么只需要执行下面脚本的最后一步，使用tar进行解压。

```bash
mkdir nps
cd nps
wget https://github.com/ehang-io/nps/releases/download/v0.26.7/linux_amd64_server.tar.gz # 架构不同，选择不同
```

解压，并进行安装。

```bash
tar xvf linux_amd64_server.tar.gz
./nps install
```

之后运行就可运行`nps`，但推荐先修改一下配置文件。在文件*./conf/nps.conf*中第40行左右，原始文件为：

```conf
web_username=admin
web_password=123
web_port = 8080
```

至少要将`web_password`修改为一个更复杂的密码，以保证网络安全。

运行时使用命令:

```bash
nps start
```

运行即可，自动在后台运行。而如果只是使用`nps`，则是进入调试模式，会输出log信息，但断开与服务器连接后`nps`也会停止运行。

### 服务器可能的坑

在阿里云服务器的常用端口之外的端口都是关闭的，其他云服务器也有可能出现这种情况，需要手动打开。

以阿里云服务器为例，首先进入在实例的后台，*更多*-*网络和安全组*-*安全组配置*之后选择*配置规则*。

![aliyun-entrance](/assets/images/intranet-penetration/aliyun-entrance.png)

在安全组规则这里，选择手动添加，协议类型选择`tcp`，端口范围可以设置区间`7000/9000`，是打开7000至9000的端口（至少包含`nps`使用的端口，默认使用为`8080`，以及应用使用的端口），授权对象则是`0.0.0.0/0`。

![firewall-port](/assets/images/intranet-penetration/firewall-port.png)


### 客户端的安装及配置

首先用你心爱的浏览器打开网址`公网服务器的公网IP:NPS的端口`，进入NPS服务端的后台。例如`120.1.1.2:8080`。

输入之前设置的NPS服务器及密码（默认为账户`admin`，密码`1234`），进入后台。

选择`客户端`，绿色`+新增`，然后直接选择最后的蓝色`+新增`即可。退回到客户端，可以看到我们新增的加客户端，ID为5。点击左侧的`加号`，记录下客户端命令，等下要用。

![](/assets/images/intranet-penetration/client-list.png)

之后同样是进入内网服务器，下载并解压缩客户端的包（不过这时候由于没有内网穿透，我们需要使用VPN后登陆），在内网服务器上进行：

```bash
mkdir npc
cd npc
wget https://github.com/ehang-io/nps/releases/download/v0.26.7/linux_amd64_client.tar.gz # 架构不同，选择不同
```

最后要运行一下客户端命令：

```bash
./npc -server=120.1.1.2:8024 -vkey=9nnc49omtv0fvez8 -type=tcp
```

需要注意此命令不要直接复制上面的内容，而是使用在新增客户端后记录的命令。而且由于这同样是运行在log模式，所以与内网的连接断开后，`npc`就会停止运行。所以建议先使用`tmux`命令，然后输入上述客户端命令，之后再断开与内网连接，`npc`也会在后台运行。`tmux`的使用场景很多，建议上网学习一个。

### 服务端的后台配置

写到这里，笔者已经很不耐烦，所以以下从简。

首先还是通过`公网IP:NPS端口`的方式进入服务端后台，在选择左侧客户端可以看到列表中服务端右侧现实已经上线（状态为开放，连接为在线，如下图ID为5的客户端）。

![client-online](/assets/images/intranet-penetration/client-online.png)

之后我们选择右侧的`TCP隧道`，然后选择新增。模式使用`TCP隧道`，`客户端ID`输入刚才看到的客户端列表中的ID，如图中的5。服务端端口可自选，2000以上端口一般都是空闲，不过注意要使用[服务器可能的坑](#服务器可能的坑)设置之内允许的端口。目标应当是`内网IP:端口`，注意是`内网IP`，而不是之前的客户端地址，而常用的端口有SSH连接的22，Jupyter默认使用放入8888，以及TensorBoard默认使用6006。注意这些端口不应当写在一起，而是分别新增三个TCP隧道。

![port matching](/assets/images/intranet-penetration/port-match.png)

最终效果如图所示，不过注意笔者的客户端ID是2，右侧IP应当是内网服务器的内网IP，而且端口并没有全都使用默认端口。

## 实际应用

如果一切就绪，那么我们就可以使用内网穿透，进行更方便地搬砖啦。

以下图设置为例，我们将公网IP的7001端口映射到了内网的22端口。假设公网IP为120.1.1.2，我们的内网账号为`goudan`。则使用SSH进行连接应当是（如果使用Putty等客户端也需要修改端口、用户、IP等信息）。

```bash
ssh -p 7001 goudan@120.1.1.2
```

进入内网服务器后，我们打开Jupyter：

```bash
jupyter notebook --port 8888 --no-browser
```

则使用`120.1.1.2:8888`即可打开Jupyter。

或者我们希望使用TensorBoard：

```bash
tensorboard --logdir=/tmp --port=8008
```

注意，上面的Jupyter和TensorBoard都建议在`tmux`下使用，不然SSH连接断开后网页就打不开了。

## 结束

趁天还没黑，快去搬砖吧！相信NPS一定能帮助你搬的又快又好！

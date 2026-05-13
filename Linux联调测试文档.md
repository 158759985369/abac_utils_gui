# ABAC GUI Linux 联调测试文档

本文档面向你的 Linux 目标机，默认仓库位置为：

```bash
~/abac_utils-master
```

GUI 目录为：

```bash
~/abac_utils-master/abac_gui
```

## 1. 先理解几个路径

### `/etc` 不是 `home`

- `/etc` 是 Linux 根目录 `/` 下的系统配置目录。
- 你的家目录是 `/home/saga`，简写为 `~`。
- 所以：

```bash
ls /etc
```

表示查看系统配置目录。

而你截图里的：

```bash
ls etc
```

是在当前目录下找一个名为 `etc` 的相对路径，所以会报错。

### 为什么 `ls /etc/abac` 提示权限不足

这说明 `/etc/abac` 已存在，但当前普通用户 `saga` 没权限读取该目录内容。

请改用：

```bash
sudo ls -l /etc/abac
```

如果只是确认目录是否存在，也可以用：

```bash
sudo test -d /etc/abac && echo exists
```

### 你当前环境里两个关键目录的含义

- `~/abac_lsm`：内核侧源码目录
- `~/abac_utils-master`：应用层/CLI 目录

而 GUI 现在是在：

```bash
~/abac_utils-master/abac_gui
```

## 2. 联调前检查

在终端进入应用层目录：

```bash
cd ~/abac_utils-master
```

依次执行：

```bash
python3 --version
which abac
abac --help
ls /sys/kernel/security/abac
sudo ls -l /etc/abac
systemctl --version
```

预期：

- `abac` 命令能找到
- `/sys/kernel/security/abac` 下至少能看到 `env_attr`、`obj_attr`、`policy`、`user_attr`
- `/etc/abac` 可以被 `sudo` 查看

## 3. 安装 GUI 依赖

先进入 GUI 目录：

```bash
cd ~/abac_utils-master/abac_gui
```

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

如果 PyQt5 缺 Qt 运行库，再安装系统包：

```bash
sudo apt update
sudo apt install -y libxcb-xinerama0 libxcb-icccm4 libxcb-keysyms1 libxcb-render-util0 libxkbcommon-x11-0
```

## 4. GUI 启动测试

### 4.1 非 root 启动测试

在 `~/abac_utils-master/abac_gui` 下执行：

```bash
python3 main.py
```

预期：

- GUI 不进入主功能
- 弹窗提示：`请以 root 权限启动本程序`

### 4.2 root 启动测试

执行：

```bash
sudo --preserve-env=DISPLAY,XAUTHORITY python3 main.py
```

预期：

- GUI 正常打开
- 能看到左侧页面：`Dashboard`、`Initialize`、`AVP`、`Users`、`Objects`、`Policies`、`Runtime & Services`

## 5. Dashboard 页面测试

打开 `Dashboard`，检查：

1. `Platform` 是否为 `Linux`
2. `Root` 是否为 `yes`
3. `abac CLI` 是否不是 `not found`
4. `/sys/kernel/security/abac` 是否显示 `ready`
5. `/etc/abac` 是否显示 `ready`
6. `/home/secured` 是否显示 `ready` 或你实际环境对应状态
7. `abac.service`、`abac_watch.service`、`abac_env.service` 状态是否能显示

如果 `/home/secured` 不存在，可以先检查：

```bash
ls -ld /home/secured
```

## 6. Initialize 页面测试

### 6.1 普通初始化

点击：

- `Run abac init`

观察：

- 结果框是否显示命令输出
- 没有异常弹窗

### 6.2 强制初始化取消测试

点击：

- `Run abac init --force`

预期：

- 先弹 GUI 确认框
- 选择 `No` 后，不执行初始化
- 结果框出现“已取消”类提示

### 6.3 强制初始化执行测试

再次点击：

- `Run abac init --force`

这次选择确认执行，然后检查：

```bash
sudo ls -l /etc/abac
sudo cat /etc/abac/avp.json
sudo cat /etc/abac/user_attr.json
sudo cat /etc/abac/obj_attr.json
sudo cat /etc/abac/policy.json
sudo cat /etc/abac/env_attr.json
```

预期：

- 5 个 json 文件都存在
- 初始化后内容结构正确

## 7. AVP 页面测试

### 7.1 新增 user AVP

在 GUI 里新增：

- 类型：`user`
- 名称：`role`
- 值：`admin,user`

然后执行：

```bash
sudo cat /etc/abac/avp.json
```

确认 `user.role` 已写入。

### 7.2 新增 obj AVP

新增：

- 类型：`obj`
- 名称：`level`
- 值：`high,low`

然后再次检查：

```bash
sudo cat /etc/abac/avp.json
```

### 7.3 修改 AVP

修改一个已有 AVP，确认：

- GUI 当前 AVP 展示更新
- `/etc/abac/avp.json` 更新

### 7.4 删除 AVP

删除一个 AVP，确认：

- GUI 展示消失
- json 中对应项消失

### 7.5 非法输入测试

故意输入：

- 带空格名字
- 非法值

确认：

- GUI 不崩溃
- 结果框能显示 CLI 错误

## 8. Users 页面测试

先确认系统里有 `abac` 组：

```bash
getent group abac
```

如果没有，需要先创建：

```bash
sudo groupadd abac
```

### 8.1 密码确认拦截测试

在 GUI 中新增用户时：

- `Password` 输入一个值
- `Confirm Password` 输入另一个不同值

预期：

- GUI 本地拦截
- 不真正执行 `abac user add`

### 8.2 正常新增用户

示例：

- 用户名：`alice`
- 至少选择一个 user 属性
- 两次密码输入相同

执行后检查：

```bash
id alice
groups alice
sudo cat /etc/abac/user_attr.json
```

预期：

- 用户创建成功
- 用户在 `abac` 组中
- `user_attr.json` 有对应记录

### 8.3 删除用户取消测试

选中一个用户点删除，确认框里点 `No`。

预期：

- 用户不被删除
- GUI 显示取消信息

### 8.4 删除用户确认测试

再次删除并确认，然后检查：

```bash
id alice
sudo cat /etc/abac/user_attr.json
```

预期：

- `id alice` 失败或提示用户不存在
- `user_attr.json` 中用户条目消失

## 9. Objects 页面测试

先确认共享目录存在：

```bash
ls -ld /home/secured
```

如果目录不存在，请先确认你的 ABAC 环境是否要求手动创建。

可以准备测试对象：

```bash
sudo mkdir -p /home/secured
sudo touch /home/secured/demo.txt
sudo chown $USER:$USER /home/secured/demo.txt
```

### 9.1 页面展示测试

打开 `Objects` 页面，确认：

- 能看到 `/home/secured` 下的条目
- 选中对象后右侧能显示当前属性

### 9.2 新增对象属性

确保先有 obj AVP，例如 `level`。

给 `demo.txt` 新增属性后检查：

```bash
sudo cat /etc/abac/obj_attr.json
```

### 9.3 修改对象属性

修改已有属性后再次检查 `obj_attr.json`。

### 9.4 删除对象属性

删除后确认 GUI 和 `obj_attr.json` 一致。

### 9.5 对象属性服务异常测试

先看服务状态：

```bash
systemctl status abac.service
```

如果服务已启用，先停掉：

```bash
sudo systemctl stop abac.service
```

然后再回 GUI 做一次对象属性写操作。

预期：

- GUI 不崩溃
- 结果框显示连接失败或服务未运行

测试完记得恢复：

```bash
sudo systemctl start abac.service
```

## 10. Policies 页面测试

先确保：

- 至少有一个 user AVP
- 至少有一个 obj AVP

### 10.1 新增规则

在 GUI 中新增一条规则，分别测试：

- `READ`
- `MODIFY`

执行后检查：

```bash
sudo cat /etc/abac/policy.json
```

确认：

- GUI 预览和最终写入规则一致

### 10.2 删除规则取消测试

删除前在确认框中点 `No`。

预期：

- 规则不变

### 10.3 删除规则确认测试

再次删除并确认，然后检查：

```bash
sudo cat /etc/abac/policy.json
```

### 10.4 顺序限制测试

如果一个 section 有多个属性，故意跳过前面的属性直接选后面的属性。

预期：

- GUI 拦截
- 提示必须按 CLI 顺序填写

## 11. Runtime & Services 页面测试

### 11.1 `abac load`

点击：

- `Run abac load`

观察：

- 结果框显示命令执行结果

### 11.2 systemd 服务控制

分别测试：

- `start`
- `stop`
- `restart`

对象：

- `abac.service`
- `abac_watch.service`
- `abac_env.service`

同时用终端复核：

```bash
systemctl status abac.service
systemctl status abac_watch.service
systemctl status abac_env.service
```

## 12. 日志与降级路径测试

每做一次写操作，检查 GUI 结果框里的：

- `Command`
- `exit_code`
- `phase`
- `stdout`
- `stderr`
- `Log file`

### 12.1 正常日志测试

如果 `/var/log/abac_gui/` 可写，确认日志文件能生成。

### 12.2 日志不可写测试

如果你愿意做额外测试，可以临时让日志目录不可写，确认：

- 命令本身仍可执行
- 最多只是日志不落盘

这个测试有风险，只有在你熟悉系统权限操作时再做。

## 13. 最重要的闭环测试

按下面顺序完整跑一遍：

1. `abac init --force`
2. 新增 user AVP
3. 新增 obj AVP
4. 新增用户
5. 在 `/home/secured` 创建测试文件
6. 给测试文件打对象属性
7. 新增策略
8. 执行 `abac load`
9. 检查 systemd 服务状态
10. 核对 `/etc/abac/*.json` 与 GUI 展示一致

## 14. 测试失败时请记录什么

如果某一步失败，请把下面 4 类信息一起发回来：

1. 你点了哪个页面、哪个按钮
2. GUI 结果框完整文本
3. 终端复核命令和输出
4. 对应配置文件内容

推荐附带这些命令输出：

```bash
pwd
which abac
systemctl status abac.service abac_watch.service abac_env.service
sudo ls -l /etc/abac
sudo cat /etc/abac/avp.json
sudo cat /etc/abac/user_attr.json
sudo cat /etc/abac/obj_attr.json
sudo cat /etc/abac/policy.json
sudo cat /etc/abac/env_attr.json
```


根据您的需求，我已将 **DeepSeek 本地安装** 相关的内容加入到了 `README` 文件中，并更新了功能部分，确保不仅支持使用付费 API，也支持本地使用 DeepSeek 大模型。以下是更新后的 `README` 文件内容：

---

# 自动求职工具

这个自动求职工具帮助用户通过 BOSS直聘或智联招聘平台，自动化上传简历和提交职位申请。通过简化的操作界面，用户可以选择平台、职位、城市，并通过脚本自动执行求职任务。除此之外，您还可以选择使用 **付费 API** 或 **本地安装的 DeepSeek 模型** 来提升求职自动化的能力。

## 功能介绍

- **智联招聘**：该工具会自动选择目标职位并直接投递简历。
- **BOSS直聘**：该工具会使用 DeepSeek R1 API，将用户的简历内容与职位要求对比，并生成一段更加凸显用户优势的话语发送给 HR，然后自动提交简历。
- **支持 DeepSeek 本地大模型**：如果您希望使用本地 DeepSeek 模型进行求职任务，也可以通过安装和配置 **DeepSeek** 模型，在本地运行，大大提升执行效率和精度。

## 安装

### 1. 安装 Google Chrome

- 请先卸载您当前的 Google Chrome 版本，以确保安装的是正确版本。
- 下载并安装 Google Chrome 版本：**109.0.5414.165**（109.0.5414.165_chrome_installer.exe）。
- 安装完成后，找到 `chrome.exe` 的安装路径，用于后续配置脚本中的 Chrome 浏览器路径。

### 2. 配置简历

- 将您的简历文件放置在项目的 `resume` 文件夹下，文件格式必须为 **PDF**。

### 3. 克隆项目并安装依赖

1. 克隆本项目到本地：

   ```bash
   git clone https://github.com/yourusername/auto-job-application.git
   cd auto-job-application
   ```

2. 安装项目依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 使用 DeepSeek 本地模型

### 1. 安装 DeepSeek 本地模型

为了使用 **DeepSeek** 模型，您需要先安装 `Ollama`。以下是 DeepSeek 本地模型的安装步骤：

1. **下载 Ollama 安装包**：
   访问 [Ollama 官方网站](https://ollama.com/)，下载并安装 `OllamaSetup.exe`（大约 745MB）。

2. **检查安装**：
   安装完成后，在命令行输入以下命令来检查是否安装成功：

   ```bash
   ollama -v
   ```

   如果成功安装，命令行会显示当前的 `ollama` 版本号。

3. **拉取 DeepSeek 模型**：
   根据您的硬件支持情况，选择适合的 DeepSeek 模型。默认情况下，您可以使用以下命令来下载 **DeepSeek 1.5b 模型**：

   ```bash
   ollama run deepseek-r1:1.5b
   ```

   如果您的硬件资源更强大，可以根据需要下载更大规模的模型。

### 2. 配置脚本使用本地 DeepSeek

如果您希望使用本地的 DeepSeek 模型，请确保已正确安装并拉取相应模型。您可以在脚本的配置部分选择是否使用本地模型或者付费 API。

- 使用 **DeepSeek 本地模型**：脚本会自动检测您的本地模型并使用它进行求职任务。
- 使用 **DeepSeek 付费 API**：如果您没有本地安装模型，脚本会自动使用 DeepSeek 提供的付费 API。

## 使用方法

### 1. 运行脚本

打开命令行，进入项目目录，运行 `main.py` 脚本：

```bash
python main_find_ui.py
```

### 2. 使用 GUI 界面

运行脚本后，会弹出图形界面（UI），您可以进行以下操作：
![img.png](img_1.png)



- **选择平台**：选择您想要投递简历的平台（BOSS直聘或智联招聘）。
- **选择职位**：输入您要投递的职位名称。
- **选择城市**：选择您希望工作的城市。
- **选择 Chrome 浏览器路径**：点击 "选择 Chrome 路径" 按钮，选择已经安装好的 `chrome.exe` 文件。
- **选择是否使用本地 DeepSeek 模型**：在脚本中配置使用本地模型或付费 API。

### 3. 检查简历

- 点击 "检查简历" 按钮，工具会验证简历是否可以正常读取，并提示简历检查结果。

### 4. 开始任务

- 点击 "开始任务" 按钮后，脚本会根据所选平台自动执行任务：
  - **BOSS直聘**：使用 DeepSeek R1 API 或本地 DeepSeek 模型生成更加突出您优势的介绍，并将简历投递。
  - **智联招聘**：直接提交简历到所选职位。

### 5. 第一次扫码

- 如果是第一次使用工具，打开浏览器时需要进行扫码（登录 BOSS直聘 或 智联招聘）。完成扫码后，之后的操作将无需再次扫码。

## 注意事项

1. **Chrome 浏览器版本**：请确保安装的是 **109.0.5414.165** 版本的 Chrome 浏览器，其他版本可能会导致脚本无法正常运行。
2. **简历格式**：简历必须放在 `resume` 文件夹下，且格式为 PDF 文件。
3. **平台支持**：目前脚本支持 BOSS直聘和智联招聘两个平台，其他平台暂不支持。
4. **DeepSeek 模型**：如果使用本地 DeepSeek 模型，请确保已经安装并拉取所需的模型版本（例如 `deepseek-r1:1.5b`）。

## 贡献

如果你希望贡献代码，修复 Bug，或添加新功能，请提交一个 Pull Request。所有贡献都非常欢迎。

## 许可证

本项目采用 [MIT 许可证](./LICENSE)，详细信息请查看 `LICENSE` 文件。


### 更新内容说明：

1. **DeepSeek 本地安装教程**：增加了关于如何安装并使用 **Ollama** 来运行 **DeepSeek 本地模型** 的详细步骤，确保用户可以选择使用付费 API 或本地安装的模型。
2. **功能说明**：在功能介绍中说明了如何使用本地模型，如何根据硬件支持下载适合的 DeepSeek 模型（例如 1.5b），并且如何在脚本中配置使用本地模型或 API。
3. **安装与配置**：详细描述了如何下载、安装 **Ollama** 并使用命令行拉取 DeepSeek 模型。

这将确保用户能够灵活选择付费 API 或本地模型的方式来执行任务。
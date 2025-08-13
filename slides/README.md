# 幻灯片查看器 (Slide Viewer)

一个功能完整的HTML幻灯片查看器，支持导航、全屏显示、导出PDF/PPT等功能。

## 功能特性

- 📖 **幻灯片浏览**: 支持前进/后退导航
- 🖱️ **多种控制方式**: 鼠标点击、键盘快捷键
- 🔍 **全屏模式**: 沉浸式演示体验
- 📄 **PDF导出**: 将所有幻灯片导出为PDF文件
- 📊 **PPT导出**: 将幻灯片导出为PowerPoint格式
- 📱 **响应式设计**: 适配不同屏幕尺寸
- ⚡ **预加载机制**: 流畅的幻灯片切换
- 🎨 **渐变文字效果**: 美观的标题样式

## 快速开始

### 方法一：使用npm脚本（推荐）

```bash
# 启动开发服务器（端口8080）
npm start

# 或者使用dev命令
npm run dev

# 使用不同端口启动
npm run serve  # 端口3000

# 自动打开浏览器预览
npm run preview
```

### 方法二：直接使用Python

```bash
# Python 3
python3 -m http.server 8080

# Python 2
python -m SimpleHTTPServer 8080
```

### 方法三：使用其他HTTP服务器

```bash
# 使用Node.js的http-server
npx http-server -p 8080

# 使用PHP内置服务器
php -S localhost:8080
```

## 访问应用

启动服务器后，在浏览器中访问：
- http://localhost:8080/slide-viewer.html

## 使用说明

### 导航控制

- **鼠标**: 点击左右箭头按钮
- **键盘快捷键**:
  - `←` / `A`: 上一张幻灯片
  - `→` / `D`: 下一张幻灯片
  - `F`: 切换全屏模式
  - `Esc`: 退出全屏模式

### 导出功能

1. **PDF导出**: 点击"导出PDF"按钮，自动生成包含所有幻灯片的PDF文件
2. **PPT导出**: 点击"导出PPT"按钮，生成PowerPoint格式文件

### 全屏模式

- 点击全屏按钮或按`F`键进入全屏模式
- 全屏模式下控制栏会自动隐藏，鼠标移动时显示
- 按`Esc`键或点击退出全屏按钮退出

## 项目结构

```
.
├── slide-viewer.html      # 主查看器文件
├── 1.html - 10.html       # 幻灯片内容文件
├── images/                # 图片资源目录
├── package.json           # 项目配置文件
└── README.md             # 项目说明文档
```

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **导出功能**: 
  - html2canvas - HTML转图片
  - jsPDF - PDF生成
  - PptxGenJS - PowerPoint生成
- **服务器**: Python HTTP Server (开发环境)

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 开发说明

### 添加新幻灯片

1. 创建新的HTML文件（如`11.html`）
2. 在`slide-viewer.html`中更新`totalSlides`变量
3. 确保新文件遵循现有的CSS类结构

### 自定义样式

幻灯片使用内联CSS样式，可以直接在各个HTML文件中修改：
- `.slide`: 幻灯片容器
- `.title`: 标题样式（支持渐变效果）
- `.content`: 内容区域

## 故障排除

### 常见问题

1. **端口被占用**: 尝试使用不同端口 `python3 -m http.server 3000`
2. **导出功能不工作**: 确保浏览器支持现代JavaScript特性
3. **幻灯片显示异常**: 检查HTML文件路径和CSS样式

### 性能优化

- 幻灯片使用预加载机制，确保流畅切换
- 图片资源建议压缩以提高加载速度
- 全屏模式下自动调整幻灯片尺寸以适配屏幕

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！
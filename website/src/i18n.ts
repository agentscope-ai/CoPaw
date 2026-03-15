export type Lang = "zh" | "en" | "ja" | "fr";

export const i18n: Record<Lang, Record<string, string>> = {
  zh: {
    "nav.docs": "文档",
    "nav.more": "更多",
    "nav.releaseNotes": "更新日志",
    "nav.download": "下载",
    "nav.github": "GitHub",
    "nav.githubComingSoon": "Coming Soon",
    "nav.lang": "EN",
    "nav.agentscopeTeam": "AgentScope",
    "hero.slogan": "懂你所需，伴你左右",
    "hero.sub":
      "你的AI个人助理；安装极简、本地与云上均可部署；支持多端接入、能力轻松扩展。",
    "hero.cta": "查看文档",
    "follow.title": "关注我们",
    "follow.sub": "第一时间获取 CoPaw 最新动态",
    "follow.xiaohongshu": "小红书：",
    "follow.x": "X：",
    "brandstory.title": "Why CoPaw？",
    "brandstory.para1":
      "CoPaw 既是「你的搭档小爪子」（co-paw），也寓意 Co Personal Agent Workstation（协同个人智能体工作台）。",
    "brandstory.para2":
      "我们希望它不是冰冷的工具，而是一只随时准备帮忙的温暖「小爪子」，是你数字生活中最默契的伙伴。",
    "features.title": "核心能力",
    "features.channels.title": "全域触达",
    "features.channels.desc":
      "支持钉钉、飞书、QQ、Discord、iMessage 等频道，一个 CoPaw 按需连接。",
    "features.private.title": "由你掌控",
    "features.private.desc":
      "记忆与个性化由你掌控，本地或云端均可；定时与协作发往指定频道。",
    "features.skills.title": "Skills 扩展",
    "features.skills.desc": "内置定时任务，自定义技能目录，CoPaw 自动加载。",
    "testimonials.title": "社区怎么说",
    "testimonials.viewAll": "查看全部",
    "testimonials.1": "CoPaw 就该这样：多频道一个入口，Python 好改好部署。",
    "testimonials.2": "定时和心跳很实用，Skills 自己加，数据都在本地。",
    "testimonials.3": "想完全掌控的团队用着很顺手。",
    "usecases.title": "你可以用 CoPaw 做什么",
    "usecases.sub": "",
    "usecases.category.social": "社交媒体",
    "usecases.category.creative": "创意与构建",
    "usecases.category.productivity": "生产力",
    "usecases.category.research": "研究与学习",
    "usecases.category.assistant": "桌面与文件",
    "usecases.category.explore": "探索更多",
    "usecases.social.1":
      "每日将小红书、知乎、Reddit 上你关注的热帖整理成摘要并推送，并根据反馈优化推荐。",
    "usecases.social.2":
      "每日抓取 B 站、YouTube 关注频道或关键词下的新视频并生成摘要，节省浏览时间。",
    "usecases.social.3":
      "分析小红书、知乎等账号的内容规律与特点，为内容创作提供参考。",
    "usecases.creative.1":
      "睡前向 CoPaw 说明目标并设定自动执行，次日即可获得可用的雏形。",
    "usecases.creative.2":
      "从选题、找素材到确定方向，CoPaw 可协助完成视频内容创作全流程。",
    "usecases.productivity.1":
      "每日汇总订阅邮件与 Newsletter 精华，并推送至钉钉、飞书或 QQ 会话。",
    "usecases.productivity.2":
      "从邮件与日历自动整理联系人，支持用自然语言查询联系人及往来记录。",
    "usecases.productivity.3":
      "记录饮食与身体反应，由 CoPaw 定期分析并呈现规律。",
    "usecases.research.1":
      "自动追踪科技与 AI 公司财报与重要资讯，筛选重点并生成摘要。",
    "usecases.research.2":
      "将链接、文章与帖子存入个人知识库，便于在多场景中检索与复用。",
    "usecases.assistant.1":
      "协助整理与搜索本地文件、阅读文档并做摘要；在钉钉、飞书或 QQ 中通过对话将指定文件发至当前会话。",
    "usecases.explore.1":
      "你可以探索更多可能，用 Skills 与定时任务组合成 agentic app。",
    "quickstart.title": "快速开始",
    "quickstart.serviceNotice":
      "几分钟，获得专属AI助理。一行命令，或双击桌面应用，自己动手，轻松搞定。",
    "quickstart.hintBefore": "安装 → 初始化 → 启动；频道配置见 ",
    "quickstart.hintLink": "文档",
    "quickstart.hintAfter": "，即可通过钉钉、飞书、QQ 等频道使用 CoPaw。",
    "quickstart.method.pip": "pip",
    "quickstart.method.script": "脚本安装",
    "quickstart.method.docker": "Docker",
    "quickstart.method.cloud": "云部署",
    "quickstart.method.desktop": "桌面应用",
    "quickstart.desc.pip": "适合自行管理 Python 环境的用户",
    "quickstart.desc.script":
      "无需手动配置 Python，一行命令自动完成安装。脚本会自动下载 uv（Python 包管理器）、创建虚拟环境、安装 CoPaw 及其依赖（含 Node.js 和前端资源）。注意：部分网络环境或企业权限管控下可能无法使用。",
    "quickstart.desc.docker":
      "使用官方 Docker 镜像快速部署，隔离环境、便于管理",
    "quickstart.desc.cloud": "云端一键部署或在线运行，无需本地环境配置",
    "quickstart.desc.desktop":
      "独立打包的桌面应用，内置完整 Python 环境、所有依赖和前端资源。双击即用，无需命令行，无需预装任何工具。",
    "quickstart.platform.mac": "macOS / Linux",
    "quickstart.platform.windows": "Windows",
    "quickstart.shell.cmd": "CMD",
    "quickstart.shell.ps": "PowerShell",
    "quickstart.docker.hub": "Docker Hub",
    "quickstart.cloud.aliyun": "阿里云",
    "quickstart.cloud.modelscope": "魔搭",
    "quickstart.cloud.aliyunDeploy": "前往阿里云一键部署",
    "quickstart.cloud.aliyunDoc": "查看说明文档",
    "quickstart.cloud.modelscopeGo": "前往魔搭创空间",
    "quickstart.desktop.platforms": "支持平台",
    "quickstart.desktop.downloadGithub": "前往 GitHub 下载",
    "quickstart.desktop.viewGuide": "查看使用指南",
    "quickstart.desktop.recommended": "推荐",
    "quickstart.badgeBeta": "Beta",
    footer: "CoPaw — 懂你所需，伴你左右",
    "footer.poweredBy.p1": "由 ",
    "footer.poweredBy.p2": " 基于 ",
    "footer.poweredBy.p3": "、",
    "footer.poweredBy.p3b": " 与 ",
    "footer.poweredBy.p4": " 打造。",
    "footer.poweredBy.team": "AgentScope 团队",
    "footer.poweredBy.agentscope": "AgentScope",
    "footer.poweredBy.runtime": "AgentScope Runtime",
    "footer.poweredBy.reme": "ReMe",
    "footer.inspiredBy": "部分灵感来源于 ",
    "footer.inspiredBy.name": "OpenClaw",
    "footer.thanksSkills": "感谢 ",
    "footer.thanksSkills.name": "anthropics/skills",
    "footer.thanksSkills.suffix": " 提供 Agent Skills 规范与示例。",
    "docs.backToTop": "返回顶部",
    "docs.copy": "复制",
    "docs.copied": "已复制",
    "docs.searchPlaceholder": "搜索文档",
    "docs.searchLoading": "加载中…",
    "docs.searchNoResults": "无结果",
    "docs.searchResultsTitle": "搜索结果",
    "docs.searchResultsTitleEmpty": "搜索文档",
    "docs.searchHint": "在左侧输入关键词后按回车搜索。",
    "releaseNotes.title": "更新日志",
    "releaseNotes.noReleases": "暂无更新日志",
  },
  en: {
    "nav.docs": "Docs",
    "nav.more": "More",
    "nav.releaseNotes": "Release Notes",
    "nav.download": "Download",
    "nav.github": "GitHub",
    "nav.githubComingSoon": "Coming Soon",
    "nav.lang": "中文",
    "nav.agentscopeTeam": "AgentScope",
    "hero.slogan": "Works for you, grows with you",
    "hero.sub":
      "Your Personal AI Assistant; easy to install, deploy on your own machine or on the cloud; supports multiple chat apps with easily extensible capabilities.",
    "hero.cta": "Read the docs",
    "follow.title": "Follow us",
    "follow.sub": "Follow us for the latest CoPaw updates",
    "follow.xiaohongshu": "Rednote:",
    "follow.x": "X:",
    "brandstory.title": "Why CoPaw?",
    "brandstory.para1":
      'CoPaw represents both a Co Personal Agent Workstation and a "co-paw"—a partner always by your side.',
    "brandstory.para2":
      'More than just a cold tool, CoPaw is a warm "little paw" always ready to lend a hand (or a paw!). It is the ultimate teammate for your digital life.',
    "features.title": "Key capabilities",
    "features.channels.title": "Every channel",
    "features.channels.desc":
      "DingTalk, Feishu, QQ, Discord, iMessage, and more — one assistant, connect as you need.",
    "features.private.title": "Under your control",
    "features.private.desc":
      "Memory and personalization under your control. Deploy locally or in the cloud; scheduled reminders and collaboration to any channel.",
    "features.skills.title": "Skills",
    "features.skills.desc":
      "Built-in Cron; custom skills in your workspace, auto-loaded.",
    "testimonials.title": "What people say",
    "testimonials.viewAll": "View all",
    "testimonials.1":
      "This is what a personal assistant should be: one entry, every channel.",
    "testimonials.2":
      "Cron and heartbeat are super practical. Add your own skills; data stays local.",
    "testimonials.3": "Teams who want full control love it.",
    "usecases.title": "What you can do with CoPaw",
    "usecases.sub": "",
    "usecases.category.social": "Social media",
    "usecases.category.creative": "Creative & building",
    "usecases.category.productivity": "Productivity",
    "usecases.category.research": "Research & learning",
    "usecases.category.assistant": "Desktop & files",
    "usecases.category.explore": "Explore more",
    "usecases.social.1":
      "Daily digest of hot posts from Xiaohongshu, Zhihu, and Reddit based on your interests, with recommendations that improve over time.",
    "usecases.social.2":
      "Daily summaries of new videos from Bilibili or YouTube by channel or keyword, saving you time browsing.",
    "usecases.social.3":
      "Analyze your Xiaohongshu or Zhihu account to uncover content patterns and inform what to post next.",
    "usecases.creative.1":
      "Describe your goal to CoPaw and set it to run overnight; get a working draft by the next day.",
    "usecases.creative.2":
      "From topic selection and material gathering to direction setting, CoPaw supports the full video content workflow.",
    "usecases.productivity.1":
      "Daily digests of newsletters and important emails, delivered to your DingTalk, Feishu or QQ chat.",
    "usecases.productivity.2":
      "Contacts surfaced from email and calendar, with natural-language search for people and past interactions.",
    "usecases.productivity.3":
      "Log diet and symptoms; CoPaw analyzes and surfaces patterns over time.",
    "usecases.research.1":
      "Track tech and AI company earnings and news; get key points and summaries automatically.",
    "usecases.research.2":
      "Save links, articles, and posts to a personal knowledge base and reuse them across workflows.",
    "usecases.assistant.1":
      "Organize and search local files, read and summarize documents; request files in DingTalk, Feishu or QQ and receive them in the current chat.",
    "usecases.explore.1":
      "Explore more possibilities—combine Skills and cron into your own agentic app.",
    "quickstart.title": "Quick start",
    "quickstart.serviceNotice":
      "Your personal AI assistant in minutes. One command, or double-click the app—do it yourself, done easily.",
    "quickstart.hintBefore":
      "Install → init → start. Configure channels to use CoPaw on DingTalk, Feishu, QQ, etc. See ",
    "quickstart.hintLink": "docs",
    "quickstart.hintAfter": ".",
    "quickstart.method.pip": "pip",
    "quickstart.method.script": "Script",
    "quickstart.method.docker": "Docker",
    "quickstart.method.cloud": "Cloud",
    "quickstart.method.desktop": "Desktop",
    "quickstart.desc.pip": "If you prefer managing Python yourself",
    "quickstart.desc.script":
      "No Python setup required, one command installs everything. The script will automatically download uv (Python package manager), create a virtual environment, and install CoPaw with all dependencies (including Node.js and frontend assets). Note: May not work in restricted network environments or corporate firewalls.",
    "quickstart.desc.docker":
      "Quick deployment with official Docker images, isolated environment and easy management",
    "quickstart.desc.cloud":
      "One-click cloud deployment or online execution, no local setup required",
    "quickstart.desc.desktop":
      "Standalone desktop app with bundled Python environment, all dependencies, and frontend assets. Double-click to run, no command line, no prerequisites required.",
    "quickstart.platform.mac": "macOS / Linux",
    "quickstart.platform.windows": "Windows",
    "quickstart.shell.cmd": "CMD",
    "quickstart.shell.ps": "PowerShell",
    "quickstart.docker.hub": "Docker Hub",
    "quickstart.cloud.aliyun": "Aliyun",
    "quickstart.cloud.modelscope": "ModelScope",
    "quickstart.cloud.aliyunDeploy": "Deploy on Aliyun ECS",
    "quickstart.cloud.aliyunDoc": "View Documentation",
    "quickstart.cloud.modelscopeGo": "Go to ModelScope Studio",
    "quickstart.desktop.platforms": "Supported Platforms",
    "quickstart.desktop.downloadGithub": "Download from GitHub",
    "quickstart.desktop.viewGuide": "View User Guide",
    "quickstart.desktop.recommended": "recommended",
    "quickstart.badgeBeta": "Beta",
    footer: "CoPaw — Works for you, grows with you",
    "footer.poweredBy.p1": "Built by ",
    "footer.poweredBy.p2": " with ",
    "footer.poweredBy.p3": ", ",
    "footer.poweredBy.p3b": ", and ",
    "footer.poweredBy.p4": ".",
    "footer.poweredBy.team": "AgentScope team",
    "footer.poweredBy.agentscope": "AgentScope",
    "footer.poweredBy.runtime": "AgentScope Runtime",
    "footer.poweredBy.reme": "ReMe",
    "footer.inspiredBy": "Partly inspired by ",
    "footer.inspiredBy.name": "OpenClaw",
    "footer.thanksSkills": "Thanks to ",
    "footer.thanksSkills.name": "anthropics/skills",
    "footer.thanksSkills.suffix": " for the Agent Skills spec and examples.",
    "docs.backToTop": "Back to top",
    "docs.copy": "Copy",
    "docs.copied": "Copied",
    "docs.searchPlaceholder": "Search docs",
    "docs.searchLoading": "Loading…",
    "docs.searchNoResults": "No results",
    "docs.searchResultsTitle": "Search results",
    "docs.searchResultsTitleEmpty": "Search docs",
    "docs.searchHint": "Enter a keyword and press Enter to search.",
    "releaseNotes.title": "Release Notes",
    "releaseNotes.noReleases": "No release notes available",
  },
  ja: {
    "nav.docs": "ドキュメント",
    "nav.more": "その他",
    "nav.releaseNotes": "更新履歴",
    "nav.download": "ダウンロード",
    "nav.github": "GitHub",
    "nav.githubComingSoon": "Coming Soon",
    "nav.lang": "EN",
    "nav.agentscopeTeam": "AgentScope",
    "hero.slogan": "あなたを理解し、寄り添う",
    "hero.sub":
      "あなたのAIパーソナルアシスタント。簡単インストール、ローカルでもクラウドでもデプロイ可能。複数チャネル対応、機能拡張も容易。",
    "hero.cta": "ドキュメントを見る",
    "follow.title": "フォローする",
    "follow.sub": "CoPaw の最新情報をいち早くお届けします",
    "follow.xiaohongshu": "小紅書：",
    "follow.x": "X：",
    "brandstory.title": "Why CoPaw？",
    "brandstory.para1":
      "CoPaw は「あなたの相棒の小さな手（co-paw）」であり、Co Personal Agent Workstation（協働パーソナルエージェントワークステーション）を意味しています。",
    "brandstory.para2":
      "冷たいツールではなく、いつでも手を差し伸べてくれる温かい「小さな手」——デジタルライフの最高のパートナーでありたいと考えています。",
    "features.title": "主な機能",
    "features.channels.title": "あらゆるチャネル",
    "features.channels.desc":
      "DingTalk、Feishu、QQ、Discord、iMessage など——ひとつのアシスタントで必要に応じて接続。",
    "features.private.title": "あなたの管理下に",
    "features.private.desc":
      "記憶とパーソナライズはあなたの管理下に。ローカルまたはクラウドにデプロイ。スケジュール通知やコラボレーションを任意のチャネルへ。",
    "features.skills.title": "Skills",
    "features.skills.desc":
      "組み込みの Cron。ワークスペースにカスタムスキルを配置すれば自動ロード。",
    "testimonials.title": "ユーザーの声",
    "testimonials.viewAll": "すべて見る",
    "testimonials.1":
      "パーソナルアシスタントはこうあるべき：ひとつの入口、すべてのチャネル。",
    "testimonials.2":
      "Cron とハートビートがとても実用的。スキルも自分で追加でき、データはローカルに保持。",
    "testimonials.3": "完全な管理を求めるチームに最適。",
    "usecases.title": "CoPaw でできること",
    "usecases.sub": "",
    "usecases.category.social": "ソーシャルメディア",
    "usecases.category.creative": "クリエイティブ＆構築",
    "usecases.category.productivity": "生産性",
    "usecases.category.research": "リサーチ＆学習",
    "usecases.category.assistant": "デスクトップ＆ファイル",
    "usecases.category.explore": "さらに探索",
    "usecases.social.1":
      "小紅書、知乎、Reddit の注目投稿を毎日ダイジェストにまとめ、フィードバックに基づいておすすめを改善。",
    "usecases.social.2":
      "Bilibili や YouTube のチャンネルやキーワードの新着動画を毎日要約し、閲覧時間を節約。",
    "usecases.social.3":
      "小紅書や知乎のアカウントを分析してコンテンツパターンを発見し、次の投稿の参考に。",
    "usecases.creative.1":
      "就寝前に CoPaw に目標を伝えて自動実行を設定すれば、翌日には動作するドラフトが完成。",
    "usecases.creative.2":
      "テーマ選定から素材収集、方向性の決定まで、CoPaw が動画コンテンツ制作のワークフロー全体をサポート。",
    "usecases.productivity.1":
      "ニュースレターや重要なメールの毎日のダイジェストを DingTalk、Feishu、QQ チャットに配信。",
    "usecases.productivity.2":
      "メールやカレンダーから連絡先を抽出し、自然言語で人物や過去のやり取りを検索。",
    "usecases.productivity.3":
      "食事や症状を記録し、CoPaw が分析して傾向を可視化。",
    "usecases.research.1":
      "テック企業や AI 企業の決算や重要ニュースを自動追跡し、要点と要約を自動生成。",
    "usecases.research.2":
      "リンク、記事、投稿を個人ナレッジベースに保存し、ワークフロー全体で再利用。",
    "usecases.assistant.1":
      "ローカルファイルの整理・検索、ドキュメントの閲覧・要約を支援。DingTalk、Feishu、QQ でリクエストしたファイルを現在のチャットに送信。",
    "usecases.explore.1":
      "さらなる可能性を探索——Skills と Cron を組み合わせて独自の agentic アプリを作成。",
    "quickstart.title": "クイックスタート",
    "quickstart.serviceNotice":
      "数分で専用AIアシスタントを取得。コマンドひとつ、またはアプリをダブルクリックするだけで簡単セットアップ。",
    "quickstart.hintBefore":
      "インストール → 初期化 → 起動。チャネル設定については ",
    "quickstart.hintLink": "ドキュメント",
    "quickstart.hintAfter":
      " をご覧ください。DingTalk、Feishu、QQ などのチャネルで CoPaw を使用できます。",
    "quickstart.method.pip": "pip",
    "quickstart.method.script": "スクリプト",
    "quickstart.method.docker": "Docker",
    "quickstart.method.cloud": "クラウド",
    "quickstart.method.desktop": "デスクトップ",
    "quickstart.desc.pip": "Python 環境を自分で管理したい方向け",
    "quickstart.desc.script":
      "Python のセットアップ不要、コマンドひとつですべてインストール。スクリプトが uv（Python パッケージマネージャー）のダウンロード、仮想環境の作成、CoPaw と依存関係（Node.js やフロントエンドアセットを含む）のインストールを自動実行します。注意：制限されたネットワーク環境や企業ファイアウォール下では動作しない場合があります。",
    "quickstart.desc.docker":
      "公式 Docker イメージによる迅速なデプロイ、隔離環境で管理が容易",
    "quickstart.desc.cloud":
      "ワンクリッククラウドデプロイまたはオンライン実行、ローカル環境の設定不要",
    "quickstart.desc.desktop":
      "Python 環境、すべての依存関係、フロントエンドアセットを同梱したスタンドアロンデスクトップアプリ。ダブルクリックで起動、コマンドライン不要、前提条件なし。",
    "quickstart.platform.mac": "macOS / Linux",
    "quickstart.platform.windows": "Windows",
    "quickstart.shell.cmd": "CMD",
    "quickstart.shell.ps": "PowerShell",
    "quickstart.docker.hub": "Docker Hub",
    "quickstart.cloud.aliyun": "Aliyun",
    "quickstart.cloud.modelscope": "ModelScope",
    "quickstart.cloud.aliyunDeploy": "Aliyun ECS にデプロイ",
    "quickstart.cloud.aliyunDoc": "ドキュメントを見る",
    "quickstart.cloud.modelscopeGo": "ModelScope Studio へ",
    "quickstart.desktop.platforms": "対応プラットフォーム",
    "quickstart.desktop.downloadGithub": "GitHub からダウンロード",
    "quickstart.desktop.viewGuide": "ユーザーガイドを見る",
    "quickstart.desktop.recommended": "おすすめ",
    "quickstart.badgeBeta": "Beta",
    footer: "CoPaw — あなたを理解し、寄り添う",
    "footer.poweredBy.p1": "",
    "footer.poweredBy.p2": " が ",
    "footer.poweredBy.p3": "、",
    "footer.poweredBy.p3b": "、および ",
    "footer.poweredBy.p4": " で構築。",
    "footer.poweredBy.team": "AgentScope チーム",
    "footer.poweredBy.agentscope": "AgentScope",
    "footer.poweredBy.runtime": "AgentScope Runtime",
    "footer.poweredBy.reme": "ReMe",
    "footer.inspiredBy": "一部のインスピレーション：",
    "footer.inspiredBy.name": "OpenClaw",
    "footer.thanksSkills": "",
    "footer.thanksSkills.name": "anthropics/skills",
    "footer.thanksSkills.suffix":
      " が Agent Skills の仕様とサンプルを提供してくれたことに感謝します。",
    "docs.backToTop": "トップに戻る",
    "docs.copy": "コピー",
    "docs.copied": "コピー済み",
    "docs.searchPlaceholder": "ドキュメントを検索",
    "docs.searchLoading": "読み込み中…",
    "docs.searchNoResults": "結果なし",
    "docs.searchResultsTitle": "検索結果",
    "docs.searchResultsTitleEmpty": "ドキュメントを検索",
    "docs.searchHint": "左側にキーワードを入力して Enter で検索。",
    "releaseNotes.title": "更新履歴",
    "releaseNotes.noReleases": "更新履歴はまだありません",
  },
  fr: {
    "nav.docs": "Documentation",
    "nav.more": "Plus",
    "nav.releaseNotes": "Notes de version",
    "nav.download": "Télécharger",
    "nav.github": "GitHub",
    "nav.githubComingSoon": "Coming Soon",
    "nav.lang": "EN",
    "nav.agentscopeTeam": "AgentScope",
    "hero.slogan": "Il vous comprend, il vous accompagne",
    "hero.sub":
      "Votre assistant personnel IA ; installation simple, déploiement local ou cloud ; prise en charge de plusieurs canaux de communication avec des capacités facilement extensibles.",
    "hero.cta": "Lire la documentation",
    "follow.title": "Suivez-nous",
    "follow.sub": "Suivez-nous pour les dernières actualités de CoPaw",
    "follow.xiaohongshu": "Xiaohongshu :",
    "follow.x": "X :",
    "brandstory.title": "Why CoPaw ?",
    "brandstory.para1":
      "CoPaw représente à la fois un Co Personal Agent Workstation et un « co-paw » — un partenaire toujours à vos côtés.",
    "brandstory.para2":
      "Plus qu'un simple outil froid, CoPaw est une « petite patte » chaleureuse, toujours prête à vous donner un coup de main (ou de patte !). C'est le compagnon idéal de votre vie numérique.",
    "features.title": "Fonctionnalités clés",
    "features.channels.title": "Tous les canaux",
    "features.channels.desc":
      "DingTalk, Feishu, QQ, Discord, iMessage et plus — un seul assistant, connectez selon vos besoins.",
    "features.private.title": "Sous votre contrôle",
    "features.private.desc":
      "Mémoire et personnalisation sous votre contrôle. Déployez localement ou dans le cloud ; rappels programmés et collaboration vers n'importe quel canal.",
    "features.skills.title": "Skills",
    "features.skills.desc":
      "Cron intégré ; compétences personnalisées dans votre espace de travail, chargées automatiquement.",
    "testimonials.title": "Ce qu'en disent les utilisateurs",
    "testimonials.viewAll": "Tout voir",
    "testimonials.1":
      "C'est ce qu'un assistant personnel devrait être : une seule entrée, tous les canaux.",
    "testimonials.2":
      "Le Cron et le heartbeat sont très pratiques. Ajoutez vos propres compétences ; les données restent en local.",
    "testimonials.3": "Les équipes qui veulent un contrôle total l'adorent.",
    "usecases.title": "Ce que vous pouvez faire avec CoPaw",
    "usecases.sub": "",
    "usecases.category.social": "Réseaux sociaux",
    "usecases.category.creative": "Création et développement",
    "usecases.category.productivity": "Productivité",
    "usecases.category.research": "Recherche et apprentissage",
    "usecases.category.assistant": "Bureau et fichiers",
    "usecases.category.explore": "Explorer davantage",
    "usecases.social.1":
      "Résumé quotidien des publications tendance de Xiaohongshu, Zhihu et Reddit selon vos centres d'intérêt, avec des recommandations qui s'améliorent au fil du temps.",
    "usecases.social.2":
      "Résumés quotidiens des nouvelles vidéos de Bilibili ou YouTube par chaîne ou mot-clé, pour vous faire gagner du temps.",
    "usecases.social.3":
      "Analysez vos comptes Xiaohongshu ou Zhihu pour découvrir des tendances de contenu et orienter vos prochaines publications.",
    "usecases.creative.1":
      "Décrivez votre objectif à CoPaw et programmez une exécution nocturne ; obtenez un brouillon fonctionnel le lendemain.",
    "usecases.creative.2":
      "Du choix du sujet à la collecte de matériaux en passant par la définition de la direction, CoPaw accompagne l'ensemble du flux de création vidéo.",
    "usecases.productivity.1":
      "Résumés quotidiens des newsletters et e-mails importants, envoyés dans votre conversation DingTalk, Feishu ou QQ.",
    "usecases.productivity.2":
      "Contacts extraits des e-mails et du calendrier, avec recherche en langage naturel des personnes et des interactions passées.",
    "usecases.productivity.3":
      "Enregistrez votre alimentation et vos symptômes ; CoPaw analyse et met en évidence les tendances au fil du temps.",
    "usecases.research.1":
      "Suivez les résultats financiers et les actualités des entreprises technologiques et IA ; obtenez automatiquement les points clés et les résumés.",
    "usecases.research.2":
      "Enregistrez des liens, articles et publications dans une base de connaissances personnelle et réutilisez-les dans vos différents flux de travail.",
    "usecases.assistant.1":
      "Organisez et recherchez des fichiers locaux, lisez et résumez des documents ; demandez des fichiers dans DingTalk, Feishu ou QQ et recevez-les dans la conversation en cours.",
    "usecases.explore.1":
      "Explorez davantage de possibilités — combinez Skills et Cron pour créer votre propre application agentique.",
    "quickstart.title": "Démarrage rapide",
    "quickstart.serviceNotice":
      "Votre assistant IA personnel en quelques minutes. Une commande ou un double-clic sur l'application — faites-le vous-même, simplement.",
    "quickstart.hintBefore":
      "Installer → initialiser → démarrer. Configurez les canaux pour utiliser CoPaw sur DingTalk, Feishu, QQ, etc. Consultez la ",
    "quickstart.hintLink": "documentation",
    "quickstart.hintAfter": ".",
    "quickstart.method.pip": "pip",
    "quickstart.method.script": "Script",
    "quickstart.method.docker": "Docker",
    "quickstart.method.cloud": "Cloud",
    "quickstart.method.desktop": "Bureau",
    "quickstart.desc.pip": "Si vous préférez gérer Python vous-même",
    "quickstart.desc.script":
      "Aucune configuration Python requise, une seule commande installe tout. Le script téléchargera automatiquement uv (gestionnaire de paquets Python), créera un environnement virtuel et installera CoPaw avec toutes ses dépendances (y compris Node.js et les ressources frontend). Note : peut ne pas fonctionner dans les environnements réseau restreints ou derrière des pare-feu d'entreprise.",
    "quickstart.desc.docker":
      "Déploiement rapide avec les images Docker officielles, environnement isolé et gestion facile",
    "quickstart.desc.cloud":
      "Déploiement cloud en un clic ou exécution en ligne, aucune configuration locale requise",
    "quickstart.desc.desktop":
      "Application de bureau autonome avec environnement Python intégré, toutes les dépendances et les ressources frontend. Double-cliquez pour lancer, sans ligne de commande, sans prérequis.",
    "quickstart.platform.mac": "macOS / Linux",
    "quickstart.platform.windows": "Windows",
    "quickstart.shell.cmd": "CMD",
    "quickstart.shell.ps": "PowerShell",
    "quickstart.docker.hub": "Docker Hub",
    "quickstart.cloud.aliyun": "Aliyun",
    "quickstart.cloud.modelscope": "ModelScope",
    "quickstart.cloud.aliyunDeploy": "Déployer sur Aliyun ECS",
    "quickstart.cloud.aliyunDoc": "Voir la documentation",
    "quickstart.cloud.modelscopeGo": "Accéder à ModelScope Studio",
    "quickstart.desktop.platforms": "Plateformes prises en charge",
    "quickstart.desktop.downloadGithub": "Télécharger depuis GitHub",
    "quickstart.desktop.viewGuide": "Voir le guide d'utilisation",
    "quickstart.desktop.recommended": "recommandé",
    "quickstart.badgeBeta": "Beta",
    footer: "CoPaw — Il vous comprend, il vous accompagne",
    "footer.poweredBy.p1": "Créé par ",
    "footer.poweredBy.p2": " avec ",
    "footer.poweredBy.p3": ", ",
    "footer.poweredBy.p3b": " et ",
    "footer.poweredBy.p4": ".",
    "footer.poweredBy.team": "l'équipe AgentScope",
    "footer.poweredBy.agentscope": "AgentScope",
    "footer.poweredBy.runtime": "AgentScope Runtime",
    "footer.poweredBy.reme": "ReMe",
    "footer.inspiredBy": "Partiellement inspiré par ",
    "footer.inspiredBy.name": "OpenClaw",
    "footer.thanksSkills": "Merci à ",
    "footer.thanksSkills.name": "anthropics/skills",
    "footer.thanksSkills.suffix":
      " pour les spécifications et exemples d'Agent Skills.",
    "docs.backToTop": "Retour en haut",
    "docs.copy": "Copier",
    "docs.copied": "Copié",
    "docs.searchPlaceholder": "Rechercher dans la documentation",
    "docs.searchLoading": "Chargement…",
    "docs.searchNoResults": "Aucun résultat",
    "docs.searchResultsTitle": "Résultats de la recherche",
    "docs.searchResultsTitleEmpty": "Rechercher dans la documentation",
    "docs.searchHint":
      "Saisissez un mot-clé et appuyez sur Entrée pour rechercher.",
    "releaseNotes.title": "Notes de version",
    "releaseNotes.noReleases": "Aucune note de version disponible",
  },
};

export function t(lang: Lang, key: string): string {
  return i18n[lang][key] ?? key;
}

# Exam Answer Extractor

CSVファイルから回答番号（1-10）を自動抽出するCLIツール

## 機能

- `inputs/`フォルダーのCSVファイルを一括処理
- OpenAI APIで回答番号を抽出
- 結果を`outputs/`フォルダーに保存

## セットアップ

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルにOpenAI API keyを設定
```

## 使い方

1. CSVファイルを`inputs/`フォルダーに配置
2. アプリケーション実行

```bash
python main.py
```

3. 結果は`outputs/`フォルダーに保存されます

## 入力仕様

- **必須カラム**: `chatgpt_output_raw`
- **対応形式**: UTF-8 CSV

## 出力仕様

- **追加カラム**: `selected_answer` (1-10の数字 or 空文字列)
- **ファイル名**: `{元ファイル名}_extracted.csv`

## 要件

- Python 3.8+
- OpenAI API key

## ディレクトリ構造

```
exam-answer-extractor/
├── main.py          # 実行ファイル
├── extractor.py     # 抽出ロジック
├── inputs/          # CSVファイル配置
├── outputs/         # 結果出力
└── logs/            # 実行ログ
```
# Exam Answer Extractor

## 新規アプリケーションにする理由
1. **単一責任の原則**: 既存アプリは「問題投げ→回答記録」、本アプリは「回答→選択番号抽出」と役割分離
2. **処理タイミングの違い**: 既存は実行時処理、本アプリは事後処理（バッチ的）
3. **依存関係の分離**: 構造化出力APIなど、異なる処理パターンを使用
4. **保守性**: 独立して改修・最適化が可能

## 概要
CSVファイルの`chatgpt_output_raw`カラムから回答番号（1-10）を抽出し、新しいカラムとして追加するCLIアプリケーション

## 機能
- `inputs/`フォルダー内のCSVファイルを自動検出・一括処理
- OpenAI APIを使用した回答番号抽出（構造化出力）
- 結果を`outputs/`フォルダーに保存
- 処理ログを`logs/`フォルダーに記録
- 処理進捗のリアルタイム表示
- エラー件数とサマリーの表示

## 入出力仕様

### 入力
- 対象フォルダー: `inputs/`
- 必須カラム: `chatgpt_output_raw`

### 出力
- 出力フォルダー: `outputs/`
- 追加カラム: `selected_answer` (1-10の数字 or 空文字列)
- ファイル名: `{元ファイル名}_extracted.csv`

## 技術スタック

### 言語・フレームワーク
- **Python 3.8+**
- **OpenAI API** (gpt-4o-mini, 構造化出力)

### 主要ライブラリ
- `openai` - OpenAI API クライアント
- `pandas` - CSV処理
- `python-dotenv` - 環境変数管理
- `pydantic` - JSON Schema定義（構造化出力用）

### 開発・実行環境
- `pip` - パッケージ管理
- `venv` - 仮想環境（推奨）

## 技術仕様
- API: OpenAI gpt-4o-mini（構造化出力）
- JSON Schema: Pydanticでレスポンス形式を定義
- プロンプト例: "以下の文章から選択された回答番号（1から10）を抽出してください"
- エラー処理: API失敗時は空文字列で継続
- ログ出力: 処理結果とエラー件数のサマリー

## ディレクトリ構造
```
/exam-answer-extractor
  ├─ main.py          # メイン実行ファイル
  ├─ extractor.py     # 抽出ロジック
  ├─ requirements.txt
  ├─ .env.example
  ├─ .gitignore
  ├─ inputs/          # CSVファイル配置
  ├─ outputs/         # 処理結果出力
  └─ logs/            # 実行ログ（gitignore対象）
```

## requirements.txt
```
openai>=1.0.0
pandas>=1.5.0
python-dotenv>=0.19.0
pydantic>=2.0.0
```
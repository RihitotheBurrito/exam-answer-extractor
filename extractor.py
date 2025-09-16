"""
Answer Extractor
OpenAI APIを使用してCSVからChatGPTの回答番号を抽出するクラス
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional
import shutil

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class AnswerResponse(BaseModel):
    """構造化出力用のレスポンスモデル"""
    selected_answer: str = Field(
        description="1から10の数字、または抽出できない場合は空文字列",
        pattern=r"^([1-9]|10|)$",
        examples=["1", "2", "10", ""]
    )
    
    @classmethod
    def validate_answer(cls, value: str) -> str:
        """回答番号のバリデーション"""
        if value == "":
            return value
        try:
            num = int(value)
            if 1 <= num <= 10:
                return str(num)
            else:
                return ""
        except ValueError:
            return ""


class AnswerExtractor:
    """CSVファイルから回答番号を抽出するクラス"""
    
    def __init__(self):
        """初期化"""
        # 環境変数読み込み
        load_dotenv()
        
        # OpenAI クライアント初期化
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
            
        self.client = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        
        # 抽出用プロンプト（requirements.mdの仕様に準拠）
        self.prompt = """以下の文章から選択された回答番号（1から10）を抽出してください。

文章に明確に「1」「2」「3」...「10」のいずれかの数字が回答として含まれている場合のみ、その数字を抽出してください。
回答番号が明確でない場合や見つからない場合は、空文字列を返してください。

例：
- 「答えは3です」→ 3
- 「選択肢2を選びます」→ 2  
- 「10番が正解だと思います」→ 10
- 「よくわかりません」→ 空文字列

文章:
{text}"""

    def extract_answer_number(self, text: str) -> str:
        """
        テキストから回答番号を抽出（エラーハンドリング強化版）
        
        Args:
            text: 抽出対象のテキスト
            
        Returns:
            str: 1-10の数字または空文字列
        """
        if not text or pd.isna(text) or str(text).strip() == "":
            return ""
            
        try:
            # OpenAI API呼び出し（構造化出力）
            completion = self.client.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "あなたは回答番号を抽出する専門AIです。与えられた文章から1から10の数字のみを正確に抽出してください。"
                    },
                    {
                        "role": "user", 
                        "content": self.prompt.format(text=str(text).strip())
                    }
                ],
                response_format=AnswerResponse,
                temperature=0,  # 一貫した結果のため
                max_tokens=50   # 短い応答のため
            )
            
            message = completion.choices[0].message
            if message.parsed and message.parsed.selected_answer:
                # 追加のバリデーション
                validated_answer = AnswerResponse.validate_answer(message.parsed.selected_answer)
                self.logger.debug(f"API応答: '{message.parsed.selected_answer}' -> 検証後: '{validated_answer}'")
                return validated_answer
            else:
                if message.refusal:
                    self.logger.warning(f"API応答拒否: {message.refusal}")
                return ""
                
        except Exception as e:
            # 詳細なエラーログ
            error_type = type(e).__name__
            
            # 特定のエラータイプに応じた処理
            if "RateLimitError" in error_type:
                self.logger.error(f"レート制限エラー: {e} - 処理を継続します")
            elif "AuthenticationError" in error_type:
                self.logger.error(f"認証エラー: {e} - API キーを確認してください")
            elif "InvalidRequestError" in error_type:
                self.logger.error(f"無効なリクエスト: {e}")
            elif "Timeout" in error_type:
                self.logger.error(f"タイムアウトエラー: {e}")
            elif "ConnectionError" in error_type:
                self.logger.error(f"接続エラー: {e}")
            else:
                self.logger.error(f"API呼び出しエラー: {error_type}: {e}")
            
            # エラー時は空文字列を返して処理を継続
            return ""

    def move_to_processed(self, input_path: Path) -> bool:
        """
        処理済みファイルをprocessed/フォルダーに移動
        
        Args:
            input_path: 移動対象のファイルパス
            
        Returns:
            bool: 移動成功時True, 失敗時False
        """
        try:
            # processedディレクトリが存在しない場合は作成
            processed_dir = Path("processed")
            processed_dir.mkdir(exist_ok=True)
            
            # 移動先のパス
            destination = processed_dir / input_path.name
            
            # 同名ファイルが既に存在する場合は番号を付ける
            counter = 1
            original_destination = destination
            while destination.exists():
                stem = original_destination.stem
                suffix = original_destination.suffix
                destination = processed_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # ファイル移動
            shutil.move(str(input_path), str(destination))
            self.logger.info(f"📁 処理済みファイルを移動: {input_path.name} → processed/{destination.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ ファイル移動エラー: {input_path.name} - {type(e).__name__}: {e}")
            return False
    
    def process_csv(self, input_path: Path) -> Tuple[int, int]:
        """
        CSVファイルを処理して回答番号を抽出
        
        Args:
            input_path: 入力CSVファイルのパス
            
        Returns:
            Tuple[int, int]: (処理済み件数, エラー件数)
        """
        try:
            # CSVファイル読み込み
            df = pd.read_csv(input_path, encoding='utf-8')
            self.logger.info(f"CSVファイル読み込み完了: {len(df)}行")
            
            # 必須カラムの確認
            if 'chatgpt_output_raw' not in df.columns:
                raise ValueError("必須カラム 'chatgpt_output_raw' が見つかりません")
            
            # selected_answerカラムを追加（既存の場合は上書き）
            df['selected_answer'] = ""
            
            processed_count = 0
            error_count = 0
            
            # 各行を処理
            for row_idx, (idx, row) in enumerate(df.iterrows()):
                row_num = row_idx + 1  # 1から始まる行番号
                
                try:
                    text = row['chatgpt_output_raw']
                    
                    # 空のテキストチェック
                    if pd.isna(text) or str(text).strip() == "":
                        self.logger.debug(f"行 {row_num}: 空のテキスト - スキップ")
                        df.at[idx, 'selected_answer'] = ""
                    else:
                        # 回答番号抽出
                        answer = self.extract_answer_number(str(text))
                        df.at[idx, 'selected_answer'] = answer
                        
                        if answer:
                            self.logger.debug(f"行 {row_num}: 抽出成功 -> '{answer}'")
                        else:
                            self.logger.debug(f"行 {row_num}: 抽出できませんでした")
                    
                    processed_count += 1
                    
                    # 進捗表示（シンプル版）
                    if row_num % 5 == 0 or row_num == len(df):
                        progress = (row_num / len(df)) * 100
                        success_rate = ((processed_count - error_count) / processed_count * 100) if processed_count > 0 else 0
                        print(f"\r  進捗: {row_num}/{len(df)} ({progress:.1f}%) | 成功率: {success_rate:.1f}%", end="", flush=True)
                        
                except Exception as e:
                    self.logger.error(f"行 {row_num} の処理エラー: {type(e).__name__}: {e}")
                    df.at[idx, 'selected_answer'] = ""
                    error_count += 1
            
            # 進捗表示完了
            print()  # 改行
            
            # 結果を保存
            output_filename = f"{input_path.stem}_extracted.csv"
            output_path = Path("outputs") / output_filename
            
            # outputsディレクトリが存在しない場合は作成
            output_path.parent.mkdir(exist_ok=True)
            
            # UTF-8 BOM付きで保存（Excel対応）
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            self.logger.info(f"結果保存完了: {output_path}")
            
            # 処理結果サマリー
            success_count = processed_count - error_count
            success_rate = (success_count / processed_count * 100) if processed_count > 0 else 0
            
            extracted_count = len(df[df['selected_answer'] != ""])
            extraction_rate = (extracted_count / len(df) * 100) if len(df) > 0 else 0
            
            self.logger.info(f"処理完了 - 成功: {success_count}/{processed_count} ({success_rate:.1f}%), 抽出成功: {extracted_count}/{len(df)} ({extraction_rate:.1f}%)")
            
            return processed_count, error_count
            
        except Exception as e:
            self.logger.error(f"CSV処理エラー: {type(e).__name__}: {e}")
            raise

    def process_csv_with_move(self, input_path: Path) -> Tuple[int, int]:
        """
        CSVファイルを処理して成功時に処理済みフォルダーに移動
        
        Args:
            input_path: 入力CSVファイルのパス
            
        Returns:
            Tuple[int, int]: (処理済み件数, エラー件数)
        """
        try:
            # CSV処理実行
            processed_count, error_count = self.process_csv(input_path)
            
            # 処理成功時に移動
            move_success = self.move_to_processed(input_path)
            if not move_success:
                self.logger.warning(f"⚠️  ファイル移動に失敗しましたが、処理は完了しています: {input_path.name}")
            
            return processed_count, error_count
            
        except Exception as e:
            self.logger.error(f"CSV処理エラー: {type(e).__name__}: {e}")
            raise
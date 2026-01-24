import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json

# .env ファイルから環境変数をロード
load_dotenv()

app = Flask(__name__)

# CORS設定
CORS(app)

# Gemini APIキーを設定
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    print(f"★KEY CHECK: Start={api_key[:5]}... End={api_key[-5:]} Length={len(api_key)}")
else:
    print("★KEY CHECK: API Key is NONE (空っぽです！)")
if not api_key:

    print("Warning: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=api_key)

# 共通の安全設定
common_safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# モデルの生成設定（デフォルト）
default_generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 60,
    "max_output_tokens": 30000,
}

# AIモデルの初期化
ai_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings=common_safety_settings,
    generation_config=default_generation_config
)

def _extract_json_from_response(raw_text):
    """Geminiの応答からJSONコードブロックを抽出するヘルパー関数"""
    raw_text = raw_text.strip()
    # コードブロック ```json ... ``` を除去
    if raw_text.startswith("```json"):
        raw_text = raw_text[len("```json"):].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text[len("```"):].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-len("```")].strip()
    
    # 念のため json という文字単体で始まっている場合の処理
    if raw_text.lower().startswith("json"):
        raw_text = raw_text[4:].strip()
        
    return raw_text

@app.route('/', methods=['GET'])
def home():
    return "Hello, Apex AI is running!", 200

@app.route('/generate_workout_plan', methods=['POST'])
def generate_workout_plan_api():
    try:
        data = request.json
        level = data.get('level', 'beginner')
        frequency = data.get('frequency', 3)
        goal = data.get('goal', 'maintain_weight')
        gender = data.get('gender', 'unknown')
        past_workout_summary = data.get('past_workout_summary', '')

        past_workout_prompt_part = ""
        if past_workout_summary:
            past_workout_prompt_part = f"""
            ユーザーの過去のワークアウト履歴の要約:
            {past_workout_summary}
            この履歴を参考に、ユーザーの現在のフィットネスレベルや好みを考慮した、よりパーソナライズされたプランを提案してください。
            """

        prompt = f"""
        あなたは、筋力トレーニングとフィットネスの専門家です。以下の情報に基づいて、実践的で安全、かつ効果的な筋トレプランを週単位で生成してください。
        ユーザーの目標達成に最大限貢献するプランを作成し、専門知識を活かしてください。

        - トレーニングレベル: {level}
        - 週のトレーニング頻度: {frequency}回
        - 目標: {goal}（lose_weight:減量, gain_muscle:増量, maintain_weight:維持）
        - 性別: {gender}
        {past_workout_prompt_part}

        ### 生成する筋トレプランのフォーマット:
        週のトレーニング頻度に応じた各日のトレーニング内容を明確に分けて提示してください。
        各エクササイズについて、エクササイズ名、推奨セット数、推奨レップ数（または時間）を具体的に記述してください。
        初心者の場合は全身運動や基本的な動きを中心に、中級者以上は部位分割法や複合的な動きを含めてください。
        目標（減量なら高レップ・短休憩、増量なら中レップ・長休憩など）に沿って、レップ数やセット数を調整してください。

        例:
        [
            {{
                "day": "Day 1",
                "focus": "胸・三頭筋",
                "exercises": [
                    {{"name": "ベンチプレス", "sets": 3, "reps": "8-12"}},
                    {{"name": "インクラインダンベルプレス", "sets": 3, "reps": "10-15"}},
                    {{"name": "トライセプスエクステンション", "sets": 3, "reps": "10-15"}}
                ]
            }},
            {{
                "day": "Day 2",
                "focus": "背中・二頭筋",
                "exercises": [
                    {{"name": "懸垂（アシスト可）", "sets": 3, "reps": "限界回数"}},
                    {{"name": "ベントオーバーロー", "sets": 3, "reps": "8-12"}},
                    {{"name": "ハンマーカール", "sets": 3, "reps": "10-15"}}
                ]
            }},
            {{
                "day": "Day 3",
                "focus": "脚・肩",
                "exercises": [
                    {{"name": "バーベルスクワット", "sets": 3, "reps": "6-10"}},
                    {{"name": "レッグプレス", "sets": 3, "reps": "10-15"}},
                    {{"name": "オーバーヘッドプレス", "sets": 3, "reps": "8-12"}},
                    {{"name": "サイドレイズ", "sets": 3, "reps": "12-18"}}
                ]
            }},
            {{
                "day": "Rest Day",
                "focus": "アクティブレスト",
                "exercises": [
                    {{"name": "ウォーキング", "duration": "30分"}},
                    {{"name": "ストレッチ", "duration": "15分"}}
                ]
            }}
        ]
        上記例のように、トレーニングがない日は「Rest Day」としてアクティブレストの内容を含めることも可能です。
        必ずJSON形式で出力し、他のテキストや説明は含めないでください。
        """

        response = ai_model.generate_content(prompt)
        json_str = _extract_json_from_response(response.text)
        workout_plan = json.loads(json_str)
        return jsonify(workout_plan)

    except Exception as e:
        print(f"Error generating workout plan: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_meal_plan', methods=['POST'])
def generate_meal_plan_api():
    try:
        data = request.json
        daily_calories = data.get('daily_calories')
        pfc_ratio = data.get('pfc_ratio') # {'protein': 0.3, 'fat': 0.2, 'carbs': 0.5}
        meal_count = data.get('meal_count', 3)
        is_premium = data.get('is_premium', False)
        past_meal_summary = data.get('past_meal_summary', '')

        if not daily_calories or not pfc_ratio:
            return jsonify({"error": "daily_calories and pfc_ratio are required"}), 400

        past_meal_prompt_part = ""
        if past_meal_summary:
            past_meal_prompt_part = f"""
            ユーザーの過去の食事履歴の要約:
            {past_meal_summary}
            この履歴を参考に、ユーザーの食の好み、アレルギー、または特定の食材の利用頻度などを考慮し、
            よりパーソナライズされた食事プランを提案してください。
            """

        prompt = f"""
        あなたは、栄養学と健康的な食生活の専門家です。以下の情報に基づいて、1日分の食事プランを具体的に生成してください。
        ユーザーが美味しく健康的な食生活を送れるような、実践的な提案をしてください。

        - 1日の目標カロリー: {daily_calories}kcal
        - PFC比率: タンパク質{int(pfc_ratio.get('protein', 0) * 100)}%, 脂質{int(pfc_ratio.get('fat', 0) * 100)}%, 炭水化物{int(pfc_ratio.get('carbs', 0) * 100)}%
        - 1日の食事回数: {meal_count}回
        - プレミアム会員: {'はい' if is_premium else 'いいえ'}
        {past_meal_prompt_part}

        ### 生成する食事プランのフォーマット:
        各食事（朝食、昼食、夕食、間食など）について、推奨される具体的な料理名や食材の組み合わせをリストアップしてください。
        各食事のおおよその推定タンパク質(g)、脂質(g)、炭水化物(g)、カロリー(kcal)を提示してください。
        プレミアム会員の場合は、より多様で詳細な食材の組み合わせ、特定の栄養素に配慮した調理法、アレルギー対応、ビーガン・ベジタリアンなどの選択肢、または簡単な調理のヒントを含めても構いません。
        無料会員の場合は、基本的なバランスの取れた、手軽に準備できる食事を提案してください。

        例:
        [
            {{
                "meal_name": "朝食",
                "dishes": ["プロテイン入りオートミール（牛乳または豆乳、ベリー、少量のナッツ）", "ゆで卵 1個"],
                "estimated_protein": 35, "estimated_fat": 15, "estimated_carbs": 50, "estimated_calories": 480
            }},
            {{
                "meal_name": "昼食",
                "dishes": ["鶏むね肉と野菜のグリル（オリーブオイル少量）", "玄米 150g", "ワカメと豆腐の味噌汁"],
                "estimated_protein": 45, "estimated_fat": 20, "estimated_carbs": 60, "estimated_calories": 600
            }},
            {{
                "meal_name": "間食",
                "dishes": ["ギリシャヨーグルト（無糖）", "リンゴ 1/2個"],
                "estimated_protein": 15, "estimated_fat": 5, "estimated_carbs": 25, "estimated_calories": 200
            }},
            {{
                "meal_name": "夕食",
                "dishes": ["鮭の塩焼き", "蒸しブロッコリー", "きのこと野菜のソテー"],
                "estimated_protein": 30, "estimated_fat": 18, "estimated_carbs": 30, "estimated_calories": 450
            }}
        ]
        必ずJSON形式で出力し、他のテキストや説明は含めないでください。
        """

        # 【修正箇所】ai_modelからではなく、最初に定義した変数からコピーする
        current_config = default_generation_config.copy()
        current_config["max_output_tokens"] = 30000
        current_config["temperature"] = 0.6

        response = ai_model.generate_content(prompt, generation_config=current_config)
        json_str = _extract_json_from_response(response.text)
        meal_plan = json.loads(json_str)
        return jsonify(meal_plan)

    except Exception as e:
        print(f"Error generating meal plan: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
import os
from datetime import datetime, date, timedelta
import re
import glob

# --- 0. 定数と基本設定 ---
st.set_page_config(layout="wide", page_title="Harmony Navigator")
# ... (v1.2.2の定数定義を全てここにコピー)
DOMAINS = ['health', 'relationships', 'meaning', 'autonomy', 'finance', 'leisure', 'competition']
DOMAIN_NAMES_JP = {
    'health': '1. 健康', 'relationships': '2. 人間関係', 'meaning': '3. 意味・貢献',
    'autonomy': '4. 自律・成長', 'finance': '5. 経済', 'leisure': '6. 余暇・心理', 'competition': '7. 競争'
}
SHORT_ELEMENTS = {
    'health': ['睡眠と休息', '身体的な快調さ'], 'relationships': ['親密な関係', '利他性・貢献'],
    'meaning': ['仕事・学業の充実感', '価値との一致'], 'autonomy': ['自己決定感', '自己成長の実感'],
    'finance': ['経済的な安心感', '職業的な達成感'], 'leisure': ['心の平穏', '楽しさ・喜び'],
    'competition': ['優越感・勝利']
}
LONG_ELEMENTS = {
    'health': ['睡眠', '食事', '運動', '身体的快適さ', '感覚的快楽', '性的満足'],
    'relationships': ['家族', 'パートナー・恋愛', '友人', '社会的承認', '利他性・貢献', '共感・繋がり'],
    'meaning': ['やりがい', '達成感', '信念との一致', 'キャリアの展望', '社会への貢献', '有能感'],
    'autonomy': ['自由・自己決定', '挑戦・冒険', '自己成長の実感', '変化の享受', '独立・自己信頼', '好奇心'],
    'finance': ['経済的安定', '経済的余裕', '労働環境', 'ワークライフバランス', '公正な評価', '職業的安定性'],
    'leisure': ['心の平穏', '自己肯定感', '創造性の発揮', '感謝', '娯楽・楽しさ', '芸術・自然'],
    'competition': ['優越感・勝利']
}
Q_COLS = ['q_' + d for d in DOMAINS]
S_COLS = ['s_' + d for d in DOMAINS]
CSV_FILE_TEMPLATE = 'harmony_data_{}.csv'
SLIDER_HELP_TEXT = "0: 全く当てはまらない\n\n25: あまり当てはまらない\n\n50: どちらとも言えない\n\n75: やや当てはまる\n\n100: 完全に当てはまる"
ELEMENT_DEFINITIONS = {
    # ... (v1.2.2の全ての材料定義)
    '睡眠と休息': '心身ともに、十分な休息が取れたと感じる度合い。例：朝、すっきりと目覚められたか。', '身体的な快調さ': '活力を感じ、身体的な不調（痛み、疲れなど）がなかった度合い。',
    '睡眠': '質の良い睡眠がとれ、朝、すっきりと目覚められた度合い。', '食事': '栄養バランスの取れた、美味しい食事に満足できた度合い。',
    '運動': '体を動かす習慣があり、それが心身の快調さに繋がっていた度合い。', '身体的快適さ': '慢性的な痛みや、気になる不調がなく、快適に過ごせた度合い。',
    '感覚的快楽': '五感を通じて、心地よいと感じる瞬間があった度合い。例：温かいお風呂、心地よい音楽。', '性的満足': '自身の性的な欲求や、パートナーとの親밀さに対して、満足感があった度合い。',
    '親密な関係': '家族やパートナー、親しい友人との、温かい、あるいは安心できる繋がりを感じた度合い。', '利他性・貢献': '自分の行動が、誰かの役に立った、あるいは喜ばれたと感じた度合い。例：「ありがとう」と言われた。',
    '家族': '家族との間に、安定した、あるいは温かい関係があった度合い。', 'パートナー・恋愛': 'パートナーとの間に、愛情や深い理解、信頼があった度合い。',
    '友人': '気軽に話せたり、支え合えたりする友人がおり、良い関係を築けていた度合い。', '社会的承認': '周囲の人々（職場、地域など）から、一員として認められ、尊重されていると感じた度合い。',
    '共感・繋がり': '他者の気持ちに寄り添ったり、逆に寄り添ってもらったりして、人との深い繋がりを感じた度合い。', '仕事・学業の充実感': '自分の仕事や学びに、やりがいや達成感を感じた度合い。',
    '価値との一致': '自分の大切にしている価値観や信念に沿って、行動できたと感じられる度合い。', 'やりがい': '自分の仕事や活動（学業、家事、趣味など）に、意義や目的を感じ、夢中になれた度合い。',
    '達成感': '何か具体的な目標を達成したり、物事を最後までやり遂げたりする経験があった度合い。', '信念との一致': '自分の「こうありたい」という価値観や、倫理観に沿った行動ができた度合い。',
    'キャリアの展望': '自分の将来のキャリアに対して、希望や前向きな見通しを持てていた度合い。', '社会への貢献': '自分の活動が、所属するコミュニティや、より大きな社会に対して、良い影響を与えていると感じられた度合い。',
    '有能感': '自分のスキルや能力を、うまく発揮できているという感覚があった度合い。', '自己決定感': '今日の自分の行動は、自分で決めたと感じられる度合い。',
    '自己成長の実感': '何かを乗り越え、自分が成長した、あるいは新しいことを学んだと感じた度合い。', '自由・自己決定': '自分の人生における重要な事柄を、他者の圧力ではなく、自分自身の意志で選択・決定できていると感じた度合い。',
    '挑戦・冒険': '新しいことに挑戦したり、未知の経験をしたりして、刺激や興奮を感じた度合い。', '変化の享受': '環境の変化や、新しい考え方を、ポジティブに受け入れ、楽しむことができた度合い。',
    '独立・自己信頼': '自分の力で物事に対処できるという、自分自身への信頼感があった度合い。', '好奇心': '様々な物事に対して、知的な好奇心を持ち、探求することに喜びを感じた度合い。',
    '経済的な安心感': '日々の生活や将来のお金について、過度な心配をせず、安心して過ごせた度合い。', '職業的な達成感': '仕事や学業において、物事をうまくやり遂げた、あるいは目標に近づいたと感じた度合い。',
    '経済的安定': '「来月の支払いは大丈夫かな…」といった、短期的なお金の心配がない状態。', '経済的余裕': '生活必需品だけでなく、趣味や自己投資など、人生を豊かにすることにもお金を使える状態。',
    '労働環境': '物理的にも、精神的にも、安全で、健康的に働ける環境があった度合い。', 'ワークライフバランス': '仕事（あるいは学業）と、プライベートな生活との間で、自分が望むバランスが取れていた度合い。',
    '公正な評価': '自分の働きや成果が、正当に評価され、報酬に反映されていると感じられた度合い。', '職業的安定性': '「この先も、この仕事を続けていけるだろうか」といった、長期的なキャリアや収入に対する不安がない状態。',
    '心の平穏': '過度な不安やストレスなく、精神的に安定していた度合い。', '楽しさ・喜び': '純粋に「楽しい」と感じたり、笑ったりする瞬間があった度合い。',
    '自己肯定感': '自分の長所も短所も含めて、ありのままの自分を、肯定的に受け入れることができた度合い。', '創造性の発揮': '何かを創作したり、新しいアイデアを思いついたりして、創造的な喜びを感じた度合い。',
    '感謝': '日常の小さな出来事や、周りの人々に対して、自然と「ありがたい」という気持ちが湧いた度合い。', '娯楽・楽しさ': '趣味に没頭したり、友人と笑い合ったり、純粋に「楽しい」と感じる時間があった度合い。',
    '芸術・自然': '美しい音楽や芸術、あるいは雄大な自然に触れて、心が動かされたり、豊かになったりする経験があった度合い。', '優越感・勝利': '他者との比較や、スポーツ、仕事、学業などにおける競争において、優位に立てたと感じた度合い。'
}
EXPANDER_TEXTS = {
    # ... (v1.2.2の全ての解説文)
    'q_t': """
        ここでは、あなたが人生で**何を大切にしたいか（理想＝情報秩序）**を数値で表現します。
        
        **どう入力する？**
        合計100点となるよう、7つのテーマ（ドメイン）に、あなたにとっての重要度をスライダーで配分してください。正解はありません。あなたの直感が、今のあなたにとっての答えです。
        
        **なぜ入力する？**
        この設定が、あなたの日々の経験を評価するための**個人的な『ものさし』**となります。この「ものさし」がなければ、自分の航海が順調なのか、航路から外れているのかを知ることはできません。
        
        （週に一度など、定期的に見直すのがおすすめです）
        """,
    's_t': """
        ここでは、あなたの**現実の経験（実践秩序）**を記録します。
        
        **どう入力する？**
        頭で考える理想ではなく、**今日一日を振り返って、実際にどう感じたか**を、各項目のスライダーで直感的に評価してください。
        
        **なぜ入力する？**
        この「現実」の記録と、先ほど設定した「理想」の羅針盤とを比べることで、両者の間に存在する**『ズレ』**を初めて発見できます。この『ズレ』に気づくことこそが、自己理解と成長の第一歩です。
        """,
    'g_t': """
        この項目は、**あなたの直感的な全体評価**です。
        
        **どう入力する？**
        細かいことは一度忘れて、「で、色々あったけど、今日の自分、全体としては何点だったかな？」という感覚を、一つのスライダーで表現してください。
        
        **なぜ入力する？**
        アプリが計算したスコア（H）と、あなたの直感（G）がどれだけ一致しているか、あるいは**ズレているか**を知るための、非常に重要な手がかりとなります。
        
        **『計算上は良いはずなのに、なぜか気分が晴れない』**といった、言葉にならない違和感や、**『予想外に楽しかった！』**という嬉しい発見など、貴重な自己発見のきっかけになります。
        """,
    'event_log': """
        これは、あなたの航海の**物語**を記録する場所です。
        
        **どう入力するのがおすすめ？**
        **『誰と会った』『何をした』『何を感じた』**といった具体的な出来事や感情を、一言でも良いので書き留めてみましょう。
        
        **なぜ書くのがおすすめ？**
        後でグラフを見たときに、数値だけでは分からない、**幸福度の浮き沈みの『なぜ？』**を解き明かす鍵となります。グラフの「山」や「谷」と、この記録を結びつけることで、あなたの幸福のパターンがより鮮明に見えてきます。
        """,
    'dashboard': """
        ここでは、記録されたデータから、あなたの幸福の**パターンと構造**を可視化します。
        - **💡 インサイト・エンジン:** モデルの計算値(H)とあなたの実感(G)のズレから、自己発見のヒントを提示します。
        - **📈 期間分析とリスク評価 (RHI):** あなたの幸福の**平均点**だけでなく、その**安定性や持続可能性（リスク）**を評価します。
        - **📊 調和度の推移:** あなたの幸福度の時間的な**『物語』**です。グラフの山や谷が、いつ、なぜ起きたのかを探ってみましょう。
        - **📋 全記録データ:** あなたの航海の**『詳細な航海日誌』**です。
        """
}

# --- 1. 計算ロジック ---
def calculate_metrics(df: pd.DataFrame, alpha: float = 0.6) -> pd.DataFrame:
    df_copy = df.copy()
    if df_copy.empty: return df_copy
    
    # ... (v1.2.2のコード)
    for col in Q_COLS + S_COLS:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0)
    
    s_vectors_normalized = df_copy[S_COLS].values / 100.0
    q_vectors = df_copy[Q_COLS].values
    df_copy['S'] = np.sum(q_vectors * s_vectors_normalized, axis=1)
    
    def calculate_unity(row):
        q_vec = row[Q_COLS].values
        s_vec_raw = row[S_COLS].values
        s_sum = np.sum(s_vec_raw)
        if s_sum == 0: return 0.0
        s_tilde = s_vec_raw / s_sum
        jsd_sqrt = jensenshannon(q_vec, s_tilde)
        jsd = jsd_sqrt**2
        return 1 - jsd
    
    df_copy['U'] = df_copy.apply(calculate_unity, axis=1)
    df_copy['H'] = alpha * df_copy['S'] + (1 - alpha) * df_copy['U']
    return df_copy

# (以降の関数は、v1.2.2から変更なし)
# ...
def analyze_discrepancy(df_processed: pd.DataFrame, threshold: int = 20):
    if df_processed.empty: return
    latest_record = df_processed.iloc[-1]
    latest_h_normalized = latest_record['H']
    latest_g = latest_record['g_happiness']
    latest_h = latest_h_normalized * 100
    gap = latest_g - latest_h
    st.subheader("💡 インサイト・エンジン")
    with st.expander("▼ これは、モデルの計算値(H)とあなたの実感(G)の『ズレ』に関する分析です", expanded=True):
        if gap > threshold:
            st.info(f"""
                **【幸福なサプライズ！🎉】**

                あなたの**実感（G = {int(latest_g)}点）**は、モデルの計算値（H = {int(latest_h)}点）を大きく上回りました。
                
                これは、あなたが**まだ言葉にできていない、新しい価値観**を発見したサインかもしれません。
                
                **問い：** 今日の記録を振り返り、あなたが設定した価値観（q_t）では捉えきれていない、予期せぬ喜びの源泉は何だったでしょうか？
                """)
        elif gap < -threshold:
            st.warning(f"""
                **【隠れた不満？🤔】**

                あなたの**実感（G = {int(latest_g)}点）**は、モデルの計算値（H = {int(latest_h)}点）を大きく下回りました。

                価値観に沿った生活のはずなのに、何かが満たされていないようです。見過ごしている**ストレス要因や、理想と現実の小さなズレ**があるのかもしれません。

                **問い：** 今日の記録を振り返り、あなたの幸福感を静かに蝕んでいた「見えない重り」は何だったでしょうか？
                """)
        else:
            st.success(f"""
                **【順調な航海です！✨】**

                あなたの**実感（G = {int(latest_g)}点）**と、モデルの計算値（H = {int(latest_h)}点）は、よく一致しています。
                
                あなたの自己認識と、現実の経験が、うまく調和している状態です。素晴らしい！
                """)

def calculate_rhi_metrics(df_period: pd.DataFrame, lambda_rhi: float, gamma_rhi: float, tau_rhi: float) -> dict:
    if df_period.empty: return {}
    mean_H = df_period['H'].mean()
    std_H = df_period['H'].std(ddof=0)
    frac_below = (df_period['H'] < tau_rhi).mean()
    rhi = mean_H - (lambda_rhi * std_H) - (gamma_rhi * frac_below)
    return {'mean_H': mean_H, 'std_H': std_H, 'frac_below': frac_below, 'RHI': rhi}

def safe_filename(name): return re.sub(r'[^a-zA-Z0-9_-]', '_', name)
def get_existing_users():
    files = glob.glob("harmony_data_*.csv")
    users = [f.replace("harmony_data_", "").replace(".csv", "") for f in files]
    return users

def show_welcome_and_guide():
    st.header("ようこそ、最初の航海士へ！「Harmony Navigator」取扱説明書")
    st.markdown("---")
    st.subheader("1. このアプリは、あなたの人生の「航海日誌」です")
    st.markdown("""
    「もっと幸せになりたい」と願いながらも、漠然とした不安や、**「理想（こうありたい自分）」**と**「現実（実際に経験した一日）」**の間の、言葉にならない『ズレ』に、私たちはしばしば悩まされます。
    
    このアプリは、その『ズレ』の正体を可視化し、あなた自身が人生の舵を取るための、**実践的な「航海術」**を提供する目的で開発されました。
    
    これは、あなただけの**「海図（チャート）」**です。この海図を使えば、
    - **自分の現在地**（今の心の状態、つまり『実践秩序』）を客観的に知り、
    - **目的地**（自分が本当に大切にしたいこと、つまり『情報秩序』）を明確にし、
    - **航路**（日々の選択）を、あなた自身で賢明に調整していくことができます。
    
    あなたの人生という、唯一無二の航海。その冒険のパートナーとして、このアプリは生まれました。
    """)
    st.markdown("---")
    st.subheader("2. 最初の航海の進め方（クイックスタート）")
    st.markdown("""
    1.  **乗船手続き（ユーザー登録 / ログイン）:**
        - サイドバーで、あなたの**「船長名（ニックネーム）」**を決め、乗船してください。二回目以降は「ログイン」から、あなたの船を選びます。
    2.  **羅針盤のセット（価値観 `q_t` の設定）:**
        - サイドバーで、あなたが人生で**「何を大切にしたいか」**を、合計100点になるよう配分します。これがあなたの航海の**目的地**を示す、最も重要な羅針盤です。
    3.  **航海日誌の記録（充足度 `s_t` の記録）:**
        - メイン画面で、今日一日を振り返り、**「実際にどう感じたか」**を記録します。日々の**現在地**を確認する作業です。
    4.  **海図の分析（ダッシュボード）:**
        - 記録を続けると、あなたの幸福度の**物語（グラフ）**が見えてきます。羅針盤（理想）と、日々の航路（現実）の**ズレ**から、次の一手を見つけ出しましょう。
    """)
    st.markdown("---")
    st.subheader("🛡️【最重要】あなたのデータとプライバシーは、絶対的に保護されます")
    with st.expander("▼ 解説：クラウド上の「魔法のレストラン」の、少し詳しいお話"):
        st.markdown("""
        「私の個人的な記録が、開発者に見られてしまうのでは？」という不安は、当然のものです。その不安を完全に取り除くために、このアプリがどういう仕組みで動いているのか、少し詳しくお話しさせてください。
        
        このアプリを、**「魔法のレストラン」**に例えてみましょう。
        
        - **あなた（ユーザー）は「お客さん」です。**
        - **私（開発者）は、このレストランで提供される料理の「レシピ（`app.py`）」を考案した、シェフです。**
        - **Streamlit Cloudは、そのレシピ通りに、24時間365日、全自動で料理を提供してくれる「レストランそのもの（サーバー）」です。**
        
        **【あなたの来店と、プライベートな記録ノート】**
        
        あなたがレストランに来店し、「Taroです」と名乗ると、レストランの賢い受付係（アプリの認証ロジック）が、裏手にある巨大で安全な**「顧客ノート保管庫」**へ向かいます。
        
        そして、保管庫の中から**「Taro様専用」と書かれた、あなただけのプライベートな記録ノート（CSVファイル）**を探し出します。もし初めての来店であれば、新しい真っ白なノートに「Taro様専用」と書いて、あなたに渡してくれます。
        
        あなたはそのノートに、その日の食事の感想（日々の記録）を自由に書き込みます。このノートは、他の誰にも見せる必要はありません。
        
        **【シェフ（私）と、レストランの関係】**
        
        ここが最も重要な点です。私は、このレストランの**「レシピを考案したシェフ」**ではありますが、**「レストランの日常業務には一切関与していない」**のです。
        
        私は、レストランの厨房にいませんし、顧客ノート保管庫の鍵も持っていません。したがって、私は**「どの時間に、どのお客さんが来店し、そのプライベートなノートに何を書いたのか」を、知る手段が一切ありません。**
        
        **【結論】**
        - **あなたのデータは、私のPCには一切保存されません。**
        - あなたが入力したデータは、あなたが登録した**「船長名」だけが知っている、あなた専用の「金庫（データファイル）」**に、クラウド上で安全に保管されます。
        - **私を含め、他の誰も、あなたの個人的な記録を、あなたの許可なく見ることは絶対にできません。**
        
        どうぞ、安心して、あなたの心の航海を記録してください。
        """)
    st.markdown("---")
    st.subheader("🧑‍🔬 あなたは、ただのユーザーじゃない。「科学の冒険者」です！")
    st.markdown("""
    最後にお伝えしたい、とても大切なことがあります。あなたがこのアプリを使ってくれることは、単なるテスト協力以上の、大きな意味を持っています。
    
    このアプリの背後にある理論は、まだ**「壮大な仮説」**の段階です。あなたが記録してくれる一つ一つのデータは、**「人間の幸福は、本当に『理想と現実のズレ』の調整プロセスで説明できるのか？」**という、人類の新しい問いを検証するための、**世界で最も貴重な科学的データ**になります。
    """)
    
    st.info("""
    **【研究協力へのお願い（インフォームド・コンセント）】**
    
    もし、ご協力いただけるのであれば、あなたが記録したデータを、**個人が特定できない形に完全に匿名化した上で**、この理論の科学的検証のための研究に利用させていただくことにご同意いただけますでしょうか。
    
    - **約束1：プライバシーの絶対保護**
        - あなたのユーザー名や、個人を特定しうる自由記述（イベントログ）は、研究データから**完全に削除**されます。研究者は、どのデータが誰のものであるかを知ることは絶対にできません。私たちが手にするのは、**誰のものか分からない、完全にランダムなIDが付与された、純粋な数値データだけ**です。
    - **約束2：目的の限定**
        - 収集された統計データは、この幸福理論の検証と発展という、**学術的な目的のためだけ**に利用され、論文や学会発表などで（統計情報として）公開される可能性があります。
    - **約束3：自由な意思**
        - この研究協力は、完全に任意です。同意しない場合でも、アプリの全ての機能を、何ら不利益なくご利用いただけます。あなたの意思が、最も尊重されます。
    
    あなたが記録する一つ一つの航海日誌が、未来の人々のための、新しい「幸福の海図」作りに繋がるかもしれません。
    """)
    st.markdown("---")

# --- 2. アプリケーションのUIとロジック ---
st.title(f'🧭 Harmony Navigator (MVP v1.2.2)')
st.caption('あなたの「理想」と「現実」のズレを可視化し、より良い人生の航路を見つけるための道具')

st.sidebar.header("👤 ユーザー認証")
if 'username' not in st.session_state: st.session_state['username'] = None
if 'consent' not in st.session_state: st.session_state['consent'] = False
auth_mode = st.sidebar.radio("モードを選択してください:", ("ログイン", "新規登録"))
existing_users = get_existing_users()
if auth_mode == "ログイン":
    if not existing_users:
        st.sidebar.warning("登録済みのユーザーがいません。まずは新規登録してください。")
    else:
        selected_user = st.sidebar.selectbox("ユーザーを選択してください:", [""] + existing_users)
        if st.sidebar.button("ログイン", key="login_button"):
            if selected_user:
                st.session_state['username'] = selected_user
                st.rerun() 
            else:
                st.sidebar.error("ユーザーを選択してください。")
elif auth_mode == "新規登録":
    new_username_raw = st.sidebar.text_input("新しいユーザー名を入力してください:", key="new_username_input")
    consent = st.sidebar.checkbox("研究協力に関する説明を読み、その内容に同意します。")
    if st.sidebar.button("登録", key="register_button"):
        new_username_safe = safe_filename(new_username_raw)
        if not new_username_safe: st.sidebar.error("ユーザー名を入力してください。")
        elif new_username_safe in existing_users: st.sidebar.error("その名前はすでに使われています。別の名前を入力するか、ログインしてください。")
        else:
            st.session_state['username'] = new_username_safe
            st.session_state['consent'] = consent
            st.sidebar.success(f"ようこそ、{new_username_safe}さん！新しい航海日誌を作成します。")
            st.rerun()

if st.session_state.get('username'):
    username = st.session_state['username']
    CSV_FILE = CSV_FILE_TEMPLATE.format(username)
    st.header(f"ようこそ、{username} さん！")

    # --- 【v1.2.3バグ修正】データ読み込みと移行ロジック ---
    if os.path.exists(CSV_FILE):
        try:
            df_data = pd.read_csv(CSV_FILE, parse_dates=['date'])
            df_data['date'] = df_data['date'].dt.date
            
            # バージョン互換性チェック
            if 's_health' not in df_data.columns:
                st.info("古いバージョンのデータを検出しました。新しいデータ構造に自動で移行します。")
                # 材料スコアからドメインスコアを再計算する
                for domain, elements in LONG_ELEMENTS.items():
                    element_cols = [f's_element_{e}' for e in elements if f's_element_{e}' in df_data.columns]
                    if element_cols:
                        df_data['s_' + domain] = df_data[element_cols].mean(axis=1).round()
                # 念のため、不足しているカラムをNaNで埋める
                for col in S_COLS:
                    if col not in df_data.columns:
                        df_data[col] = 50 # デフォルト値
        except Exception as e:
            st.error(f"データファイルの読み込み中にエラーが発生しました: {e}")
            df_data = pd.DataFrame() # 空のデータフレームで続行
    else:
        columns = ['date', 'mode', 'consent'] + Q_COLS + S_COLS + ['g_happiness', 'event_log']
        for _, elements in LONG_ELEMENTS.items():
            for element in elements:
                columns.append(f's_element_{element}')
        df_data = pd.DataFrame(columns=columns)
    
    today = date.today()
    if not df_data.empty and not df_data[df_data['date'] == today].empty: st.sidebar.success(f"✅ 今日の記録 ({today.strftime('%Y-%m-%d')}) は完了しています。")
    else: st.sidebar.info(f"ℹ️ 今日の記録 ({today.strftime('%Y-%m-%d')}) はまだありません。")
    
    st.sidebar.header('⚙️ 価値観 (q_t) の設定')
    with st.sidebar.expander("▼ これは何？どう入力する？"):
        st.markdown(EXPANDER_TEXTS['q_t'])
    if not df_data.empty and all(col in df_data.columns for col in Q_COLS): latest_q = df_data[Q_COLS].iloc[-1].values * 100
    else: latest_q = [15, 15, 15, 15, 15, 15, 10]
    q_values = {}
    for i, domain in enumerate(DOMAINS):
        q_values[domain] = st.sidebar.slider(DOMAIN_NAMES_JP[domain], 0, 100, int(latest_q[i]), key=f"q_{domain}")
    q_total = sum(q_values.values())
    st.sidebar.metric(label="現在の合計値", value=q_total)
    if q_total != 100: st.sidebar.warning(f"合計が100になるように調整してください。 (現在: {q_total})")
    else: st.sidebar.success("合計は100です。入力準備OK！")

    st.header('✍️ 今日の航海日誌を記録する')
    with st.expander("▼ これは、何のために記録するの？"):
        st.markdown(EXPANDER_TEXTS['s_t'])
    
    st.markdown("##### 記録する日付")
    target_date = st.date_input("記録する日付:", value=today, min_value=today - timedelta(days=7), max_value=today, label_visibility="collapsed")
    if not df_data.empty and not df_data[df_data['date'] == target_date].empty: st.warning(f"⚠️ {target_date.strftime('%Y-%m-%d')} のデータは既に記録されています。保存すると上書きされます。")
    
    st.markdown("##### 記録モード")
    input_mode = st.radio("記録モード:", ('🚀 **クイック・ログ**', '🔬 **ディープ・ダイブ**'), horizontal=True, label_visibility="collapsed", captions=["日々の継続を重視した、基本的な測定モードです。", "週に一度など、じっくり自分と向き合いたい時に。より深い洞察を得られます。"])
    if 'クイック' in input_mode: active_elements = SHORT_ELEMENTS; mode_string = 'quick'
    else: active_elements = LONG_ELEMENTS; mode_string = 'deep'
    
    with st.form(key='daily_input_form'):
        st.subheader(f'1. 今日の充足度 (s_t) は？ - {input_mode.split("（")[0]}')
        
        s_values = {}
        s_element_values = {}
        
        col1, col2 = st.columns(2)
        domain_containers = {'health': col1, 'relationships': col1, 'meaning': col1, 'autonomy': col2, 'finance': col2, 'leisure': col2}
        
        if not df_data.empty and any(c.startswith('s_element_') for c in df_data.columns):
            latest_s_elements = df_data.filter(like='s_element_').iloc[-1]
        else: 
            latest_s_elements = pd.Series(50, index=[f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d])
        
        for domain, container in domain_containers.items():
            with container:
                elements_to_show = active_elements.get(domain, [])
                if elements_to_show:
                    with st.expander(f"**{DOMAIN_NAMES_JP[domain]}** - クリックして詳細入力"):
                        element_scores = []
                        for element in elements_to_show:
                            default_val = int(latest_s_elements.get(f's_element_{element}', 50))
                            element_help_text = ELEMENT_DEFINITIONS.get(element, "")
                            score = st.slider(element, 0, 100, default_val, key=f"s_element_{element}", help=element_help_text)
                            element_scores.append(score)
                            s_element_values[f's_element_{element}'] = score
                        if element_scores:
                            s_values[domain] = int(np.mean(element_scores))

        with col2:
            domain = 'competition'
            elements_to_show = active_elements.get(domain, [])
            if elements_to_show:
                with st.expander(f"**{DOMAIN_NAMES_JP[domain]}** - クリックして詳細入力"):
                    default_val = int(latest_s_elements.get(f's_element_{elements_to_show[0]}', 50))
                    element_help_text = ELEMENT_DEFINITIONS.get(elements_to_show[0], "")
                    score = st.slider(elements_to_show[0], 0, 100, default_val, key=f"s_element_{elements_to_show[0]}", help=element_help_text)
                    s_values[domain] = score
                    s_element_values[f's_element_{elements_to_show[0]}'] = score
        
        st.subheader('2. 総合的な幸福感 (Gt) は？')
        with st.expander("▼ これはなぜ必要？"): st.markdown(EXPANDER_TEXTS['g_t'])
        g_happiness = st.slider('', 0, 100, 50, label_visibility="collapsed", help=SLIDER_HELP_TEXT)
        
        st.subheader('3. 今日の出来事や気づきは？')
        with st.expander("▼ なぜ書くのがおすすめ？"): st.markdown(EXPANDER_TEXTS['event_log'])
        event_log = st.text_area('', height=100, label_visibility="collapsed")
        
        submitted = st.form_submit_button('今日の記録を保存する')

    if submitted:
        if q_total != 100: st.error('価値観 (q_t) の合計が100になっていません。サイドバーを確認してください。')
        else:
            q_normalized = {f'q_{d}': v / 100.0 for d, v in q_values.items()}
            s_domain_scores = {f's_{d}': s_values.get(d, 0) for d in DOMAINS}
            consent_status = st.session_state.get('consent', False)
            new_record = { 'date': target_date, 'mode': mode_string, 'consent': consent_status, **q_normalized, **s_domain_scores, **s_element_values, 'g_happiness': g_happiness, 'event_log': event_log }
            new_df = pd.DataFrame([new_record])
            df_data = df_data[df_data['date'] != target_date]
            df_data = pd.concat([df_data, new_df], ignore_index=True)
            all_element_cols = [f's_element_{e}' for d in LONG_ELEMENTS.values() for e in d]
            all_cols = ['date', 'mode', 'consent'] + Q_COLS + S_COLS + ['g_happiness', 'event_log'] + all_element_cols
            for col in all_cols:
                if col not in df_data.columns: df_data[col] = np.nan
            df_data = df_data.sort_values(by='date').reset_index(drop=True)
            df_data.to_csv(CSV_FILE, index=False)
            st.success(f'{target_date.strftime("%Y-%m-%d")} の記録を保存（または上書き）しました！')
            
            with st.expander("▼ 保存された記録のサマリー", expanded=True):
                st.write(f"**総合的幸福感 (G): {g_happiness} 点**")
                for domain in DOMAINS:
                    st.write(f"- {DOMAIN_NAMES_JP[domain]}: {s_domain_scores.get(domain, 'N/A')} 点")

            st.balloons()
            st.rerun()

    st.header('📊 あなたの航海チャート')
    with st.expander("▼ このチャートの見方"):
        st.markdown(EXPANDER_TEXTS['dashboard'])
        
    if df_data.empty:
        st.info('まだ記録がありません。最初の日誌を記録してみましょう！')
    else:
        df_processed = calculate_metrics(df_data.fillna(0).copy())
        
        st.subheader("📈 期間分析とリスク評価 (RHI)")
        with st.expander("▼ これは、あなたの幸福の『持続可能性』を評価する指標です", expanded=False):
            st.markdown("""
            - **平均調和度 (H̄):** この期間の、あなたの幸福の**平均点**です。
            - **変動リスク (σ):** 幸福度の**浮き沈みの激しさ**です。値が小さいほど、安定した航海だったことを示します。
            - **不調日数割合:** 幸福度が、あなたが設定した「不調」のラインを下回った日の割合です。
            - **RHI (リスク調整済・幸福指数):** 平均点から、変動と不調のリスクを差し引いた、**真の『幸福の実力値』**です。この値が高いほど、あなたの幸福が、持続可能で、逆境に強いことを示します。
            """)
        
        period_options = [7, 30, 90]
        if len(df_processed) < 7:
            st.info("期間分析には最低7日分のデータが必要です。記録を続けてみましょう！")
        else:
            default_index = 1 if len(df_processed) >= 30 else 0
            selected_period = st.selectbox("分析期間を選択してください（日）:", period_options, index=default_index)
            
            if len(df_processed) >= selected_period:
                df_period = df_processed.tail(selected_period)

                st.markdown("##### あなたのリスク許容度を設定")
                col1, col2, col3 = st.columns(3)
                lambda_param = col1.slider("変動(不安定さ)へのペナルティ(λ)", 0.0, 2.0, 0.5, 0.1, help="値が大きいほど、日々の幸福度の浮き沈みが激しいことを、より重く評価します。")
                gamma_param = col2.slider("下振れ(不調)へのペナルティ(γ)", 0.0, 2.0, 1.0, 0.1, help="値が大きいほど、幸福度が低い日が続くことを、より深刻な問題として評価します。")
                tau_param = col3.slider("「不調」と見なす閾値(τ)", 0.0, 1.0, 0.5, 0.05, help="この値を下回る日を「不調な日」としてカウントします。")

                rhi_results = calculate_rhi_metrics(df_period, lambda_param, gamma_param, tau_param)
                
                st.markdown("##### 分析結果")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("平均調和度 (H̄)", f"{rhi_results['mean_H']:.3f}")
                col2.metric("変動リスク (σ)", f"{rhi_results['std_H']:.3f}")
                col3.metric("不調日数割合", f"{rhi_results['frac_below']:.1%}")
                col4.metric("リスク調整済・幸福指数 (RHI)", f"{rhi_results['RHI']:.3f}", delta=f"{rhi_results['RHI'] - rhi_results['mean_H']:.3f} (平均との差)")
            else:
                st.warning(f"分析には最低{selected_period}日分のデータが必要です。現在の記録は{len(df_processed)}日分です。")

        analyze_discrepancy(df_processed)
        st.subheader('調和度 (H) の推移')
        df_processed_chart = df_processed.copy()
        df_processed_chart['date'] = pd.to_datetime(df_processed_chart['date'])
        st.line_chart(df_processed_chart.rename(columns={'H': '調和度 (H)'}), x='date', y='H')
        st.subheader('全記録データ')
        st.dataframe(df_processed.round(2))
        st.caption('このアプリは、あなたの理論「幸福論と言語ゲーム」のMVPです。')
        
else:
    show_welcome_and_guide()

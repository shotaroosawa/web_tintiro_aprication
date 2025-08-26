from flask import Flask, render_template, request, jsonify, redirect, url_for
import random

def judge(num_A, num_B, num_C):
    """
    サイコロの目を判定し、役とスコアを返します。
    """
    dice_sorted = sorted([num_A, num_B, num_C])
    if num_A == 1 and num_B == 1 and num_C == 1:
        return {"score": 100, "message": "ピンゾロ"}
    elif dice_sorted == [4, 5, 6]:
        return {"score": 60, "message": "456だぜ！"}
    elif num_A == num_B and num_B == num_C:
        return {"score": 80, "message": "ゾロ目だぜ！"}
    elif dice_sorted == [1, 2, 3]:
        return {"score": 0, "message": "123だぜ！"}
    elif dice_sorted[0] == dice_sorted[1] or \
         dice_sorted[1] == dice_sorted[2]: # ゾロ目でない場合の2つ一致も含む
        return {"score": 50, "message": "払い戻し"}
    else:
        return {"score": 10, "message": "目無しだぜ！"}

def check(PL1, PL2):
    """
    2人のプレイヤーのスコアを比較し、勝敗を判定します。
    """
    if PL1 > PL2:
        return "勝ち"
    elif PL1 < PL2:
        return "負け"
    else:
        return "引き分け"

def checkpoint(PL1, PL2, dice_a, dice_b, dice_c):
    """
    勝敗と役に応じてポイントの倍率を計算します。
    """
    point = 1.0
    if PL1 > PL2:
        if dice_a == 1 and dice_b == 1 and dice_c == 1:
            point = 5.0
        elif dice_a == dice_b and dice_b == dice_c: # ゾロ目
            point = 3.0
        elif sorted([dice_a, dice_b, dice_c]) == [4, 5, 6]:
            point = 2.0
        elif dice_a == dice_b or dice_a == dice_c or dice_b == dice_c: # 払い戻し
            point = 1.0
        elif sorted([dice_a, dice_b, dice_c]) == [1, 2, 3]: # 123
            point = 0.5
    else: # PL1がPL2以下の場合（負けまたは引き分け）
        point = -1.0
    return point

app = Flask(__name__)

# ゲームの状態（グローバル変数、シンプル化のため）
player1_points = 1000.0
player2_points = 1000.0

@app.route("/")
def home():
    """
    タイトル画面を表示します。
    """
    return render_template("title.html")

@app.route("/game")
def game_page():
    """
    ゲーム画面を初期状態で表示します。
    """
    global player1_points, player2_points
    # ゲーム開始時にポイントをリセット
    player1_points = 1000.0
    player2_points = 1000.0
    
    return render_template(
        "index.html",
        player1_points=int(player1_points),
        player2_points=int(player2_points),
        # ゲーム開始前の初期表示
        dice_p1=[0, 0, 0],
        dice_p2=[0, 0, 0],
        message_p1="サイコロを振って勝負！",
        message_p2="サイコロを振って勝負！",
        result_p1="",
        result_p2="",
        game_started=False # 初回レンダリングではゲームはまだ始まっていない
    )

@app.route("/roll_dice_ajax", methods=["POST"])
def roll_dice_ajax():
    """
    サイコロを振り、結果をJSONで返します。
    """
    global player1_points, player2_points
    
    bet = request.json.get("bet", 0)

    # Player 1's turn
    dice_p1 = [random.randint(1, 6) for _ in range(3)]
    result_p1_data = judge(dice_p1[0], dice_p1[1], dice_p1[2])
    
    # Player 2's turn (ここでは便宜上、同時に振る)
    dice_p2 = [random.randint(1, 6) for _ in range(3)]
    result_p2_data = judge(dice_p2[0], dice_p2[1], dice_p2[2])
    
    # 勝敗判定
    winner_p1_status = check(result_p1_data["score"], result_p2_data["score"])
    
    # ポイント更新
    if winner_p1_status == "勝ち":
        point_p1_mult = checkpoint(result_p1_data["score"], result_p2_data["score"], dice_p1[0], dice_p1[1], dice_p1[2])
        player1_points += bet * point_p1_mult
        player2_points -= bet * point_p1_mult
    elif winner_p1_status == "負け":
        player1_points -= bet
        player2_points += bet
    # 引き分けの場合はポイント変動なし

    return jsonify({
        "dice_p1": dice_p1,
        "message_p1": result_p1_data["message"],
        "dice_p2": dice_p2,
        "message_p2": result_p2_data["message"],
        "result_p1": winner_p1_status,
        "result_p2": check(result_p2_data["score"], result_p1_data["score"]), # プレイヤー2視点での勝敗
        "player1_points": int(player1_points),
        "player2_points": int(player2_points),
        "game_started": True
    })

if __name__ == "__main__":
    app.run(debug=True)
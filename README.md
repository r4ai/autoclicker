# AutoClicker

シンプルで使いやすい自動クリッカー。GUI 操作でクリック間隔・ボタン・回数を設定し、ホットキーで素早く開始・停止できます。

## 機能

- クリック間隔を時・分・秒・ミリ秒単位で細かく設定
- マウスボタン（左・右・中）を選択
- シングルクリック / ダブルクリックを切り替え
- 無限リピートまたは指定回数リピート
- ホットキーによるグローバル制御（ウィンドウが非アクティブでも動作）

## ホットキー

| キー | 動作                       |
| ---- | -------------------------- |
| `F6` | 開始 / 停止の切り替え      |
| `F7` | 緊急停止（常に確実に停止） |

## インストール

### 実行ファイル（Windows）

[Releases](https://github.com/r4ai/autoclicker/releases) ページから `autoclicker.exe` をダウンロードして実行するだけです。インストール不要。

### ソースから実行

[uv](https://docs.astral.sh/uv/) が必要です。

```bash
git clone https://github.com/r4ai/autoclicker.git
cd autoclicker
uv run autoclicker
```

## 使い方

1. **Click Interval** — クリックの間隔を設定します。
2. **Click Options** — マウスボタンとクリック種別（シングル / ダブル）を選択します。
3. **Repeat** — 無限リピートか回数指定かを選択します。
4. `Start [F6]` ボタンを押すか `F6` キーを押して開始します。
5. 停止するには `Stop [F6]` ボタン、`F6`、または `F7`（緊急停止）を使います。

## 開発

```bash
# 依存関係のインストール
uv sync

# 実行
uv run autoclicker

# exe ビルド
uv run pyinstaller --onefile --windowed --name autoclicker autoclicker.py
```

## ライセンス

MIT
